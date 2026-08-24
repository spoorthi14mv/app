import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from models import db
from models.customer import Customer
from models.prediction import Prediction
from services.model_trainer import ModelTrainer
from services.prediction_service import PredictionService

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/prediction', methods=['GET'])
def index():
    return render_template('prediction.html')

@prediction_bp.route('/predict', methods=['POST'])
def predict_single():
    data = request.form.to_dict()
    # Convert numeric fields
    for k in ['tenure', 'monthly_charges', 'total_charges']:
        if k in data and data[k]:
            data[k] = float(data[k])

    service = PredictionService()
    result = service.predict_single(data)

    return jsonify(result)

@prediction_bp.route('/bulk-predict', methods=['POST'])
def predict_bulk():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)

            # Normalize columns
            df.columns = [str(c).lower().strip() for c in df.columns]

            service = PredictionService()
            result_df, error = service.predict_bulk(df)

            if error:
                return jsonify({'error': error})

            # Aggregate stats to return to frontend for charts
            stats = {
                'churn_dist': {
                    'labels': ['Predicted Churn (Yes)', 'Predicted Stay (No)'],
                    'data': [
                        int((result_df['predicted_churn'] == 'Yes').sum()),
                        int((result_df['predicted_churn'] == 'No').sum())
                    ]
                },
                'risk_dist': {
                    'labels': ['High', 'Medium', 'Low'],
                    'data': [
                        int((result_df['risk_level'] == 'High').sum()),
                        int((result_df['risk_level'] == 'Medium').sum()),
                        int((result_df['risk_level'] == 'Low').sum())
                    ]
                },
                'contract_dist': {
                    'labels': [],
                    'datasets': [
                        {'label': 'High Risk', 'data': []},
                        {'label': 'Medium Risk', 'data': []},
                        {'label': 'Low Risk', 'data': []}
                    ]
                }
            }

            # Group by contract
            if 'contract' in result_df.columns:
                contracts = result_df['contract'].unique().tolist()
                stats['contract_dist']['labels'] = contracts
                for risk in ['High', 'Medium', 'Low']:
                    risk_data = []
                    for contract in contracts:
                        c_df = result_df[(result_df['contract'] == contract) & (result_df['risk_level'] == risk)]
                        risk_data.append(int(len(c_df)))
                    stats['contract_dist']['datasets'][['High', 'Medium', 'Low'].index(risk)]['data'] = risk_data

            return jsonify({
                'success': 'Bulk predictions completed and saved to database.',
                'stats': stats
            })
        except Exception as e:
            return jsonify({'error': str(e)})

@prediction_bp.route('/train', methods=['POST'])
def train_model():
    # Load current customers from DB to train
    customers = Customer.query.all()
    if len(customers) < 100:
        return jsonify({'error': 'Not enough data to train. Please upload a larger dataset.'})

    data = []
    for c in customers:
        data.append({
            'customer_id': c.customer_id,
            'gender': c.gender,
            'senior_citizen': c.senior_citizen,
            'partner': c.partner,
            'dependents': c.dependents,
            'tenure': c.tenure,
            'phone_service': c.phone_service,
            'multiple_lines': c.multiple_lines,
            'internet_service': c.internet_service,
            'online_security': c.online_security,
            'online_backup': c.online_backup,
            'device_protection': c.device_protection,
            'tech_support': c.tech_support,
            'streaming_tv': c.streaming_tv,
            'streaming_movies': c.streaming_movies,
            'contract': c.contract,
            'paperless_billing': c.paperless_billing,
            'payment_method': c.payment_method,
            'monthly_charges': c.monthly_charges,
            'total_charges': c.total_charges,
            'churn': c.churn
        })

    df = pd.DataFrame(data)

    trainer = ModelTrainer()
    result = trainer.train_and_evaluate(df)

    if "error" in result:
        return jsonify({'error': result["error"]})

    return jsonify({
        'success': True,
        'message': f"Training complete. Best model: {result['best_model']}",
        'results': result['results']
    })

@prediction_bp.route('/customers')
def customers():
    filter_risk = request.args.get('risk', '')

    query = db.session.query(Customer, Prediction).filter(
        Customer.customer_id == Prediction.customer_id
    )

    if filter_risk:
        query = query.filter(Prediction.risk_level == filter_risk)

    results = query.limit(100).all()

    return render_template('customers.html', results=results, filter_risk=filter_risk)

from sqlalchemy import func

@prediction_bp.route('/segments')
def segments():
    total_customers = db.session.query(Customer).count() or 1

    def get_segment_stats(query):
        count = query.count()
        if count == 0:
            return {'count': 0, 'percent': 0, 'churn_rate': 0, 'avg_tenure': 0, 'avg_charges': 0}

        # Calculate stats for this segment
        avg_t = query.with_entities(func.avg(Customer.tenure)).scalar() or 0
        avg_c = query.with_entities(func.avg(Customer.monthly_charges)).scalar() or 0

        churned = query.filter(Customer.churn == 'Yes').count()

        return {
            'count': count,
            'percent': round((count / total_customers) * 100, 1),
            'churn_rate': round((churned / count) * 100, 1),
            'avg_tenure': round(avg_t, 1),
            'avg_charges': round(avg_c, 2)
        }

    # 1. High Value - Low Risk
    q1 = db.session.query(Customer).outerjoin(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.monthly_charges > 70, (Prediction.risk_level == 'Low') | (Prediction.risk_level.is_(None))
    )
    s1 = get_segment_stats(q1)

    # 2. High Value - High Risk
    q2 = db.session.query(Customer).join(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.monthly_charges > 70, Prediction.risk_level == 'High'
    )
    s2 = get_segment_stats(q2)

    # 3. Long-Term Loyal
    q3 = db.session.query(Customer).outerjoin(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.tenure > 60, (Prediction.risk_level == 'Low') | (Prediction.risk_level.is_(None))
    )
    s3 = get_segment_stats(q3)

    # 4. New Customers
    q4 = db.session.query(Customer).filter(Customer.tenure <= 12)
    s4 = get_segment_stats(q4)

    segments_data = {
        'high_value_low_risk': s1,
        'high_value_high_risk': s2,
        'long_term_loyal': s3,
        'new_customers': s4
    }

    return render_template('segments.html', segments=segments_data, total=total_customers)

@prediction_bp.route('/api/segments/charts')
def api_segments_charts():
    total_customers = db.session.query(Customer).count() or 1

    q1 = db.session.query(Customer).outerjoin(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.monthly_charges > 70, (Prediction.risk_level == 'Low') | (Prediction.risk_level.is_(None))
    )
    q2 = db.session.query(Customer).join(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.monthly_charges > 70, Prediction.risk_level == 'High'
    )
    q3 = db.session.query(Customer).outerjoin(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.tenure > 60, (Prediction.risk_level == 'Low') | (Prediction.risk_level.is_(None))
    )
    q4 = db.session.query(Customer).filter(Customer.tenure <= 12)

    counts = [q1.count(), q2.count(), q3.count(), q4.count()]
    labels = ['High Value/Low Risk', 'High Value/High Risk', 'Long-Term Loyal', 'New Customers']

    # Calculate churns
    def get_churns(q):
        if q.count() == 0: return 0
        return q.filter(Customer.churn == 'Yes').count()

    churns = [get_churns(q1), get_churns(q2), get_churns(q3), get_churns(q4)]

    return jsonify({
        'distribution': {
            'labels': labels,
            'data': counts
        },
        'churn': {
            'labels': labels,
            'data': churns
        }
    })
