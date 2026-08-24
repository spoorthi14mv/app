from flask import Blueprint, render_template, jsonify
from services.recommendation_engine import RecommendationEngine
from models import db
from models.customer import Customer
from models.prediction import Prediction
from sqlalchemy import func

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/insights')
def index():
    insights = RecommendationEngine.get_insights()
    recommendations = RecommendationEngine.get_customer_recommendations()
    return render_template('insights.html', insights=insights, recommendations=recommendations)

@insights_bp.route('/api/insights/charts')
def api_charts():
    # Only return data if predictions exist
    if db.session.query(Prediction).count() == 0:
        return jsonify({'error': 'No predictions available.'})

    # 1. Risk Distribution
    risk_counts = db.session.query(Prediction.risk_level, func.count(Prediction.id)).group_by(Prediction.risk_level).all()
    risk_dict = {k: v for k, v in risk_counts if k is not None}

    # 2. High Risk Segments (Contract based for simplicity)
    hr_contracts = db.session.query(Customer.contract, func.count(Customer.id)).join(Prediction, Customer.customer_id == Prediction.customer_id).filter(Prediction.risk_level == 'High').group_by(Customer.contract).all()

    # 3. Risk Factors (Top reasons high risk customers are high risk)
    # Since we calculate reasons dynamically in get_customer_recommendations, we will approximate here using overall high-risk stats
    hr_no_tech = db.session.query(func.count(Customer.id)).join(Prediction).filter(Prediction.risk_level == 'High', Customer.tech_support == 'No').scalar() or 0
    hr_mtm = db.session.query(func.count(Customer.id)).join(Prediction).filter(Prediction.risk_level == 'High', Customer.contract == 'Month-to-month').scalar() or 0
    hr_fiber = db.session.query(func.count(Customer.id)).join(Prediction).filter(Prediction.risk_level == 'High', Customer.internet_service == 'Fiber optic').scalar() or 0
    hr_new = db.session.query(func.count(Customer.id)).join(Prediction).filter(Prediction.risk_level == 'High', Customer.tenure <= 12).scalar() or 0

    avg_charge = db.session.query(func.avg(Customer.monthly_charges)).scalar() or 0
    hr_high_charge = db.session.query(func.count(Customer.id)).join(Prediction).filter(Prediction.risk_level == 'High', Customer.monthly_charges > avg_charge).scalar() or 0

    return jsonify({
        'risk_dist': {
            'labels': ['Low', 'Medium', 'High'],
            'data': [risk_dict.get('Low', 0), risk_dict.get('Medium', 0), risk_dict.get('High', 0)]
        },
        'high_risk_segments': {
            'labels': [c[0] for c in hr_contracts],
            'data': [c[1] for c in hr_contracts]
        },
        'risk_factors': {
            'labels': ['No Tech Support', 'Month-to-Month', 'Fiber Optic', 'New Customers (<=1yr)', 'High Monthly Charges'],
            'data': [hr_no_tech, hr_mtm, hr_fiber, hr_new, hr_high_charge]
        }
    })
