import os
import joblib
import pandas as pd
from flask import current_app
from models import db
from models.prediction import Prediction

class PredictionService:
    def __init__(self):
        self.model = None
        self.pipeline = None
        self.load_model()

    def load_model(self):
        models_dir = current_app.config['MODELS_DIR']
        model_path = os.path.join(models_dir, 'model.joblib')
        pipeline_path = os.path.join(models_dir, 'preprocessing.joblib')

        if os.path.exists(model_path) and os.path.exists(pipeline_path):
            self.model = joblib.load(model_path)
            self.pipeline = joblib.load(pipeline_path)
            return True
        return False

    def predict_single(self, customer_data):
        if not self.model or not self.pipeline:
            if not self.load_model():
                return {"error": "Model not trained yet."}

        df = pd.DataFrame([customer_data])

        # Apply preprocessing
        try:
            for col, le in self.pipeline['encoders'].items():
                if col in df.columns:
                    # Handle unseen categories safely
                    known_classes = list(le.classes_)
                    df[col] = df[col].apply(lambda x: x if x in known_classes else known_classes[0])
                    df[col] = le.transform(df[col].astype(str))
                else:
                    df[col] = 0 # Default if missing

            if len(self.pipeline['num_cols']) > 0:
                for col in self.pipeline['num_cols']:
                    if col not in df.columns:
                        df[col] = 0.0
                df[self.pipeline['num_cols']] = self.pipeline['scaler'].transform(df[self.pipeline['num_cols']])

            # Ensure columns match training
            X = pd.DataFrame()
            for col in self.pipeline['features']:
                X[col] = df[col] if col in df.columns else 0.0

            # Predict
            if hasattr(self.model, "predict_proba"):
                prob = self.model.predict_proba(X)[0][1]
            else:
                prob = float(self.model.predict(X)[0])

            pred = "Yes" if prob > 0.5 else "No"

            risk = "LOW"
            if prob > 0.6:
                risk = "HIGH"
            elif prob >= 0.3:
                risk = "MEDIUM"

            return {
                "probability": round(prob * 100, 1),
                "prediction": pred,
                "risk_level": risk
            }
        except Exception as e:
            return {"error": str(e)}

    def predict_bulk(self, df):
        if not self.model or not self.pipeline:
            if not self.load_model():
                return None, "Model not trained yet."

        results = []
        try:
            # Keep original for returning
            orig_df = df.copy()

            for col, le in self.pipeline['encoders'].items():
                if col in df.columns:
                    known_classes = list(le.classes_)
                    df[col] = df[col].apply(lambda x: x if x in known_classes else known_classes[0])
                    df[col] = le.transform(df[col].astype(str))
                else:
                    df[col] = 0

            if len(self.pipeline['num_cols']) > 0:
                for col in self.pipeline['num_cols']:
                    if col not in df.columns:
                        df[col] = 0.0
                df[self.pipeline['num_cols']] = self.pipeline['scaler'].transform(df[self.pipeline['num_cols']])

            X = pd.DataFrame()
            for col in self.pipeline['features']:
                X[col] = df[col] if col in df.columns else 0.0

            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(X)[:, 1]
            else:
                probs = self.model.predict(X)

            orig_df['churn_probability'] = np.round(probs * 100, 1)
            orig_df['predicted_churn'] = ['Yes' if p > 0.5 else 'No' for p in probs]

            def get_risk(p):
                if p > 0.6: return "HIGH"
                if p >= 0.3: return "MEDIUM"
                return "LOW"

            orig_df['risk_level'] = [get_risk(p) for p in probs]

            # Save predictions to DB (optional, simplified here)
            # Clear old predictions
            db.session.query(Prediction).delete()

            predictions = []
            for i, row in orig_df.iterrows():
                p = Prediction(
                    customer_id=str(row.get('customer_id', f'CUST_{i}')),
                    churn_probability=row['churn_probability'],
                    predicted_churn=row['predicted_churn'],
                    risk_level=row['risk_level'],
                    model_name="Selected Model"
                )
                predictions.append(p)

            db.session.bulk_save_objects(predictions)
            db.session.commit()

            return orig_df, None

        except Exception as e:
            return None, str(e)
