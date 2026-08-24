from flask import Blueprint, render_template, jsonify
from models import db
from models.prediction import Prediction
from services.churn_analyzer import ChurnAnalyzer

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def index():
    kpis = ChurnAnalyzer.get_dashboard_kpis()
    # Add High Risk count from Predictions
    high_risk_count = db.session.query(Prediction).filter(Prediction.risk_level == 'HIGH').count()
    kpis['high_risk'] = high_risk_count

    return render_template('dashboard.html', kpis=kpis)

@dashboard_bp.route('/api/dashboard/charts')
def api_charts():
    chart_data = ChurnAnalyzer.get_chart_data()
    return jsonify(chart_data)
