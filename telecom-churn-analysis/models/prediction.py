from models import db
from datetime import datetime

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), index=True, nullable=False)
    churn_probability = db.Column(db.Float)
    predicted_churn = db.Column(db.String(20))
    risk_level = db.Column(db.String(20), index=True)
    model_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prediction {self.customer_id} - {self.risk_level}>'
