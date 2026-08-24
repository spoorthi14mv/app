import pandas as pd
from io import BytesIO
from models import db
from models.customer import Customer
from models.prediction import Prediction
from services.churn_analyzer import ChurnAnalyzer

class ReportGenerator:
    @staticmethod
    def generate_excel_report():
        # Get KPIs
        kpis = ChurnAnalyzer.get_dashboard_kpis()
        kpi_df = pd.DataFrame([{
            'Total Customers': kpis['total_customers'],
            'Churned Customers': kpis['churned'],
            'Active Customers': kpis['active'],
            'Churn Rate': kpis['churn_rate'],
            'Avg Monthly Charges': kpis['avg_charges'],
            'Avg Tenure': kpis['avg_tenure']
        }])

        # Get Customers with Predictions
        query = db.session.query(
            Customer.customer_id,
            Customer.tenure,
            Customer.contract,
            Customer.monthly_charges,
            Customer.churn,
            Prediction.churn_probability,
            Prediction.risk_level
        ).outerjoin(Prediction, Customer.customer_id == Prediction.customer_id).all()

        customers_df = pd.DataFrame(query, columns=[
            'Customer ID', 'Tenure', 'Contract', 'Monthly Charges',
            'Actual Churn', 'Churn Probability (%)', 'Risk Level'
        ])

        # Write to BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            kpi_df.to_excel(writer, sheet_name='Summary KPIs', index=False)
            customers_df.to_excel(writer, sheet_name='Customer Data', index=False)

        output.seek(0)
        return output
