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

        total_churned = db.session.query(func.count(Customer.id)).filter(Customer.churn == 'Yes').scalar() or 0

        if total_churned == 0:
            insights.append({
                'title': 'Excellent Retention',
                'metric': '0% Churn',
                'observation': 'There are currently no churned customers in the dataset.',
                'action': 'Continue with current retention strategies.',
                'type': 'success'
            })
            return insights

        # Overall Churn Rate
        churn_rate = (total_churned / total_customers) * 100
        insights.append({
            'title': 'Overall Churn Rate',
            'metric': f'{churn_rate:.1f}%',
            'observation': f'Out of {total_customers} customers, {total_churned} have churned.',
            'action': 'Set an organizational goal to reduce this rate by 5% next quarter.',
            'type': 'primary' if churn_rate < 20 else 'danger'
        })

        avg_charges = db.session.query(func.avg(Customer.monthly_charges)).scalar() or 0

        # 1. High Monthly Charges
        high_charge_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.monthly_charges > avg_charges,
            Customer.churn == 'Yes'
        ).scalar() or 0
        high_charge_total = db.session.query(func.count(Customer.id)).filter(Customer.monthly_charges > avg_charges).scalar() or 1
        high_charge_rate = (high_charge_churn / high_charge_total) * 100

        if high_charge_rate > churn_rate:
            insights.append({
                'title': 'Price Sensitivity',
                'metric': f'{high_charge_rate:.1f}% churn for > ₹{avg_charges:.0f}/mo',
                'observation': 'Customers paying above the average monthly charge are churning faster than the general population.',
                'action': 'Offer personalized discounts, bundle upgrades, or value-add services to high-paying accounts.',
                'type': 'warning'
            })

        # 2. Contract Types
        contracts = db.session.query(Customer.contract, func.count(Customer.id)).filter(Customer.churn == 'Yes').group_by(Customer.contract).all()
        if contracts:
            highest_risk_contract = max(contracts, key=lambda x: x[1])
            insights.append({
                'title': 'Contract Risk',
                'metric': f'{highest_risk_contract[1]} lost on {highest_risk_contract[0]}',
                'observation': f'The {highest_risk_contract[0]} contract type accounts for the highest volume of churn.',
                'action': 'Provide loyalty benefits or price locks for customers who upgrade to longer-term contracts.',
                'type': 'danger'
            })

        # 3. Internet Service
        internet_services = db.session.query(Customer.internet_service, func.count(Customer.id)).filter(Customer.churn == 'Yes', Customer.internet_service != 'No').group_by(Customer.internet_service).all()
        if internet_services:
            highest_risk_internet = max(internet_services, key=lambda x: x[1])
            insights.append({
                'title': 'Internet Service Quality',
                'metric': f'{highest_risk_internet[1]} lost on {highest_risk_internet[0]}',
                'observation': f'Customers using {highest_risk_internet[0]} internet have the highest churn volume among internet users.',
                'action': 'Investigate service reliability and competitor pricing for this specific internet tier.',
                'type': 'info'
            })

        # 4. Technical Support
        no_tech_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.tech_support == 'No',
            Customer.churn == 'Yes'
        ).scalar() or 0
        no_tech_total = db.session.query(func.count(Customer.id)).filter(Customer.tech_support == 'No').scalar() or 1
        no_tech_rate = (no_tech_churn / no_tech_total) * 100

        if no_tech_rate > churn_rate:
            insights.append({
                'title': 'Support Impact',
                'metric': f'{no_tech_rate:.1f}% churn without Tech Support',
                'observation': 'Customers without technical support are highly vulnerable to churning.',
                'action': 'Offer proactive technical assistance or free tech support trials to high-risk customers.',
                'type': 'warning'
            })

        # 5. Tenure
        new_cust_churn = db.session.query(func.count(Customer.id)).filter(
            Customer.tenure <= 12,
            Customer.churn == 'Yes'
        ).scalar() or 0
        new_cust_total = db.session.query(func.count(Customer.id)).filter(Customer.tenure <= 12).scalar() or 1
        new_cust_rate = (new_cust_churn / new_cust_total) * 100

        if new_cust_rate > churn_rate:
            insights.append({
                'title': 'Early Attrition',
                'metric': f'{new_cust_rate:.1f}% churn within 1st year',
                'observation': 'A significant portion of new customers leave within their first 12 months.',
                'action': 'Deploy an aggressive 90-day onboarding program with check-in calls to ensure satisfaction.',
                'type': 'danger'
            })

        return insights

    @staticmethod
    def get_customer_recommendations(limit=50):
        # Join Customer and Prediction tables based on customer_id
        # Order by highest probability to prioritize genuinely high-risk cases
        results = db.session.query(Customer, Prediction).join(
            Prediction, Customer.customer_id == Prediction.customer_id
        ).filter(
            Prediction.risk_level == 'High'
        ).order_by(Prediction.churn_probability.desc()).limit(limit).all()

        recommendations = []
        avg_charges = db.session.query(func.avg(Customer.monthly_charges)).scalar() or 0

        for customer, prediction in results:
            reason = []
            actions = []
            priority = "Medium"

            if customer.contract == 'Month-to-month':
                reason.append("Short contract")
                actions.append("Offer contract upgrade with 1st month free")
                priority = "High"

            if customer.monthly_charges > avg_charges:
                reason.append("High monthly charges")
                actions.append("Provide targeted service discount or bundle offer")
                priority = "High"

            if customer.tech_support == 'No' and customer.internet_service != 'No':
                reason.append("No Tech Support")
                actions.append("Offer free 3-month tech support trial")

            if customer.tenure <= 12:
                reason.append("Low tenure")
                actions.append("Trigger onboarding check-in call")

            if not reason:
                reason.append("General high risk")
                actions.append("Assign to personal retention campaign")

            recommendations.append({
                'customer_id': customer.customer_id,
                'probability': prediction.churn_probability,
                'risk': prediction.risk_level,
                'reason': " + ".join(reason),
                'action': " | ".join(actions),
                'priority': priority
            })

        return recommendations
