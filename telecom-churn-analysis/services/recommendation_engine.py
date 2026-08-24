from models import db
from models.customer import Customer
from models.prediction import Prediction
from sqlalchemy import func

class RecommendationEngine:
    @staticmethod
    def get_insights():
        insights = []
        total_customers = db.session.query(func.count(Customer.id)).scalar() or 0

        if total_customers == 0:
            return insights

        avg_charges = db.session.query(func.avg(Customer.monthly_charges)).scalar() or 0

        # 1. High Monthly Charges
        high_charge_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.monthly_charges > avg_charges,
            Customer.churn == 'Yes'
        ).scalar() or 0

        if high_charge_churn > 0:
            insights.append({
                'title': 'High Monthly Charges',
                'observation': 'Customers with higher than average monthly charges show increased churn.',
                'action': 'Offer personalized discounts or lower-cost plans to high-risk customers.',
                'type': 'warning'
            })

        # 2. Month-to-Month Contracts
        mtm_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.contract == 'Month-to-month',
            Customer.churn == 'Yes'
        ).scalar() or 0

        if mtm_churn > 0:
            insights.append({
                'title': 'Month-to-Month Contracts',
                'observation': 'Short-term contract customers have higher churn.',
                'action': 'Provide loyalty benefits for customers who upgrade to one-year or two-year contracts.',
                'type': 'danger'
            })

        # 3. Technical Support
        no_tech_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.tech_support == 'No',
            Customer.churn == 'Yes'
        ).scalar() or 0

        if no_tech_churn > 0:
            insights.append({
                'title': 'Technical Support',
                'observation': 'Customers without technical support may have higher churn.',
                'action': 'Offer proactive technical assistance to high-risk customers.',
                'type': 'info'
            })

        # 4. New Customers
        new_cust_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.tenure < 12,
            Customer.churn == 'Yes'
        ).scalar() or 0

        if new_cust_churn > 0:
            insights.append({
                'title': 'New Customers',
                'observation': 'Customers with low tenure (under 1 year) have higher churn risk.',
                'action': 'Create onboarding and early-stage loyalty programs.',
                'type': 'primary'
            })

        return insights

    @staticmethod
    def get_customer_recommendations(limit=50):
        # Join Customer and Prediction tables based on customer_id
        results = db.session.query(Customer, Prediction).filter(
            Customer.customer_id == Prediction.customer_id,
            Prediction.risk_level == 'HIGH'
        ).limit(limit).all()

        recommendations = []
        avg_charges = db.session.query(func.avg(Customer.monthly_charges)).scalar() or 0

        for customer, prediction in results:
            reason = "High risk profile"
            action = "Review account"
            priority = "Medium"

            if customer.contract == 'Month-to-month' and prediction.churn_probability > 70:
                reason = "High risk + Short contract"
                action = "Recommend contract upgrade incentive"
                priority = "High"
            elif customer.monthly_charges > avg_charges and prediction.churn_probability > 70:
                reason = "High risk + High charges"
                action = "Offer personalized discount"
                priority = "High"
            elif customer.tech_support == 'No' and prediction.churn_probability > 70:
                reason = "High risk + No Tech Support"
                action = "Offer free tech support trial"
                priority = "Medium"

            recommendations.append({
                'customer_id': customer.customer_id,
                'probability': prediction.churn_probability,
                'risk': prediction.risk_level,
                'reason': reason,
                'action': action,
                'priority': priority
            })

        return recommendations
