from flask import Blueprint, render_template, send_file
from flask_login import login_required
from models import db
from models.model_result import ModelResult
from services.report_generator import ReportGenerator

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    model_results = ModelResult.query.all()
    return render_template('reports.html', models=model_results)

@reports_bp.route('/reports/export')
@login_required
def export_excel():
    output = ReportGenerator.generate_excel_report()
    return send_file(
        output,
        download_name='Telecom_Churn_Report.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
