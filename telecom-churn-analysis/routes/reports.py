from flask import Blueprint, render_template, send_file
from models import db
from models.model_result import ModelResult
from services.report_generator import ReportGenerator

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def index():
    from services.churn_analyzer import ChurnAnalyzer
    from services.recommendation_engine import RecommendationEngine

    kpis = ChurnAnalyzer.get_dashboard_kpis()
    insights = RecommendationEngine.get_insights()

    return render_template('reports.html', kpis=kpis, insights=insights)

@reports_bp.route('/reports/export')
def export_excel():
    output = ReportGenerator.generate_excel_report()
    return send_file(
        output,
        download_name='Telecom_Churn_Report.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
