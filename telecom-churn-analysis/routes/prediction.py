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
            _, error = service.predict_bulk(df)

            if error:
                return jsonify({'error': error})

            return jsonify({'success': 'Bulk predictions completed and saved to database.'})
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

@prediction_bp.route('/segments')
def segments():
    # Basic aggregation for segments
    high_value_low_risk = db.session.query(Customer).join(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.monthly_charges > 70, Prediction.risk_level == 'LOW'
    ).count()

    high_value_high_risk = db.session.query(Customer).join(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.monthly_charges > 70, Prediction.risk_level == 'HIGH'
    ).count()

    long_term_loyal = db.session.query(Customer).join(Prediction, Customer.customer_id == Prediction.customer_id).filter(
        Customer.tenure > 60, Prediction.risk_level == 'LOW'
    ).count()

    new_customers = db.session.query(Customer).filter(Customer.tenure <= 12).count()

    segments_data = {
        'high_value_low_risk': high_value_low_risk,
        'high_value_high_risk': high_value_high_risk,
        'long_term_loyal': long_term_loyal,
        'new_customers': new_customers
    }

    return render_template('segments.html', segments=segments_data)
