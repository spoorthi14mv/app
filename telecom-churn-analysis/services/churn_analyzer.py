import pandas as pd
from models import db
from models.customer import Customer
from sqlalchemy import func

class ChurnAnalyzer:
    @staticmethod
    def get_dashboard_kpis():
        total = db.session.query(func.count(Customer.id)).scalar() or 0
        if total == 0:
            return {
                'total_customers': 0, 'churned': 0, 'active': 0,
                'churn_rate': '0.0%', 'retention_rate': '0.0%', 'avg_charges': 0.0, 'avg_tenure': 0.0
            }

        churned = db.session.query(func.count(Customer.id)).filter(Customer.churn == 'Yes').scalar() or 0
        active = total - churned
        churn_rate = (churned / total) * 100
        retention_rate = (active / total) * 100

        avg_charges = db.session.query(func.avg(Customer.monthly_charges)).scalar() or 0.0
        avg_tenure = db.session.query(func.avg(Customer.tenure)).scalar() or 0.0

        return {
            'total_customers': total,
            'churned': churned,
            'active': active,
            'churn_rate': f"{churn_rate:.1f}%",
            'retention_rate': f"{retention_rate:.1f}%",
            'avg_charges': round(avg_charges, 2),
            'avg_tenure': round(avg_tenure, 1)
        }

    @staticmethod
    def get_chart_data():
        total = db.session.query(func.count(Customer.id)).scalar() or 0
        if total == 0:
            return {}

        # 1. Churn Distribution
        churned = db.session.query(func.count(Customer.id)).filter(Customer.churn == 'Yes').scalar() or 0
        stayed = total - churned
        churn_dist = {'labels': ['Churned', 'Stayed'], 'data': [churned, stayed]}

        # Helper to group by a column
        def get_dist_by_col(col_name):
            col_attr = getattr(Customer, col_name)
            data = db.session.query(col_attr, func.count(Customer.id)).group_by(col_attr).all()
            return {k: v for k, v in data if k is not None}

        def get_churn_dist_by_col(col_name):
            col_attr = getattr(Customer, col_name)
            # Count Yes and No for each category
            yes_data = db.session.query(col_attr, func.count(Customer.id)).filter(Customer.churn == 'Yes').group_by(col_attr).all()
            no_data = db.session.query(col_attr, func.count(Customer.id)).filter(Customer.churn == 'No').group_by(col_attr).all()

            yes_dict = {k: v for k, v in yes_data if k is not None}
            no_dict = {k: v for k, v in no_data if k is not None}

            labels = list(set(list(yes_dict.keys()) + list(no_dict.keys())))
            yes_counts = [yes_dict.get(l, 0) for l in labels]
            no_counts = [no_dict.get(l, 0) for l in labels]

            return {
                'labels': labels,
                'datasets': [
                    {'label': 'Churned', 'data': yes_counts},
                    {'label': 'Stayed', 'data': no_counts}
                ]
            }

        # 2. Churn by Contract
        contract_churn = get_churn_dist_by_col('contract')

        # 3. Churn by Tenure Group (0-12, 13-24, etc.)
        # Done simply in Python after fetching
        tenure_data = db.session.query(Customer.tenure, Customer.churn).all()
        bins = [0, 12, 24, 36, 48, 60, 100]
        labels = ['0-1y', '1-2y', '2-3y', '3-4y', '4-5y', '>5y']
        tenure_groups = {l: {'Yes': 0, 'No': 0} for l in labels}

        for t, c in tenure_data:
            if t is None: continue
            for i, b in enumerate(bins[1:]):
                if t <= b:
                    lbl = labels[i]
                    c_val = 'Yes' if c == 'Yes' else 'No'
                    tenure_groups[lbl][c_val] += 1
                    break

        tenure_churn = {
            'labels': labels,
            'datasets': [
                {'label': 'Churned', 'data': [tenure_groups[l]['Yes'] for l in labels]},
                {'label': 'Stayed', 'data': [tenure_groups[l]['No'] for l in labels]}
            ]
        }

        # 4. Monthly Charges by Churn
        charges_data = db.session.query(Customer.churn, func.avg(Customer.monthly_charges)).group_by(Customer.churn).all()
        charges_dict = {k: v for k, v in charges_data if k is not None}
        avg_charges_churn = {
            'labels': ['Churned', 'Stayed'],
            'data': [round(charges_dict.get('Yes', 0) or 0, 2), round(charges_dict.get('No', 0) or 0, 2)]
        }

        # 5. Churn by Payment Method
        payment_churn = get_churn_dist_by_col('payment_method')

        # 6. Churn by Internet Service
        internet_churn = get_churn_dist_by_col('internet_service')

        # 7. Tenure vs Monthly Charges Scatter Approximation (Avg Monthly Charges per Tenure Group)
        # Using the same tenure labels
        tenure_charges_groups = {l: [] for l in labels}
        tenure_charges_data = db.session.query(Customer.tenure, Customer.monthly_charges).all()
        for t, m in tenure_charges_data:
            if t is None or m is None: continue
            for i, b in enumerate(bins[1:]):
                if t <= b:
                    lbl = labels[i]
                    tenure_charges_groups[lbl].append(m)
                    break

        avg_charges_tenure = {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Avg Monthly Charges',
                    'data': [round(sum(tenure_charges_groups[l])/len(tenure_charges_groups[l]), 2) if tenure_charges_groups[l] else 0 for l in labels]
                }
            ]
        }

        return {
            'churn_dist': churn_dist,
            'contract_churn': contract_churn,
            'tenure_churn': tenure_churn,
            'avg_charges_churn': avg_charges_churn,
            'payment_churn': payment_churn,
            'internet_churn': internet_churn,
            'avg_charges_tenure': avg_charges_tenure
        }
