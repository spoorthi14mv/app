from flask import Blueprint, render_template
from flask_login import login_required
from services.churn_analyzer import ChurnAnalyzer

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis')
@login_required
def index():
    # Pass initial data or let frontend fetch via API
    kpis = ChurnAnalyzer.get_dashboard_kpis()
    return render_template('analysis.html', kpis=kpis)
