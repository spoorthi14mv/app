from models import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), index=True, nullable=False)

    gender = db.Column(db.String(20))
    senior_citizen = db.Column(db.Integer)
    partner = db.Column(db.String(20))
    dependents = db.Column(db.String(20))

    tenure = db.Column(db.Integer)
    phone_service = db.Column(db.String(20))
    multiple_lines = db.Column(db.String(50))
    internet_service = db.Column(db.String(50))
    online_security = db.Column(db.String(50))
    online_backup = db.Column(db.String(50))
    device_protection = db.Column(db.String(50))
    tech_support = db.Column(db.String(50))
    streaming_tv = db.Column(db.String(50))
    streaming_movies = db.Column(db.String(50))

    contract = db.Column(db.String(50), index=True)
    paperless_billing = db.Column(db.String(20))
    payment_method = db.Column(db.String(100))

    monthly_charges = db.Column(db.Float)
    total_charges = db.Column(db.Float)

    churn = db.Column(db.String(20), index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Customer {self.customer_id}>'
