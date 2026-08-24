import os
import joblib
import pandas as pd
import numpy as np
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
        pipeline_path = os.path.join(models_dir, 'pipeline.joblib')

        if os.path.exists(pipeline_path):
            self.pipeline = joblib.load(pipeline_path)
            return True
        return False

    def predict_single(self, customer_data):
        if not self.pipeline:
            if not self.load_model():
                return {"error": "No trained model is available. Please upload a dataset containing both Churn=Yes and Churn=No records."}

        df = pd.DataFrame([customer_data])

        try:
            # Get expected features from the pipeline's ColumnTransformer
            expected_num_cols = self.pipeline.named_steps['preprocessor'].transformers_[0][2]
            expected_cat_cols = self.pipeline.named_steps['preprocessor'].transformers_[1][2]

            for col in expected_num_cols:
                if col not in df.columns:
                    df[col] = 0.0
            for col in expected_cat_cols:
                if col not in df.columns:
                    df[col] = 'Unknown'

            # Ensure TotalCharges is numeric, coercing blanks to NaN, then fill
            if 'total_charges' in df.columns:
                df['total_charges'] = pd.to_numeric(df['total_charges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')

            # Fill NaNs
            cat_cols = df.select_dtypes(include=['object']).columns.tolist()
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            for col in num_cols:
                df[col] = df[col].fillna(0.0)
            for col in cat_cols:
                df[col] = df[col].fillna('Unknown')

            # Select exactly the features the pipeline expects
            all_features = expected_num_cols + expected_cat_cols
            X = df[all_features]

            # Predict
            if hasattr(self.pipeline, "predict_proba"):
                prob = self.pipeline.predict_proba(X)[0][1]
            else:
                prob = float(self.pipeline.predict(df)[0])

            pred = "Yes" if prob > 0.5 else "No"

            risk = "Low"
            if prob >= 0.7:
                risk = "High"
            elif prob >= 0.4:
                risk = "Medium"

            return {
                "probability": round(prob * 100, 1),
                "prediction": pred,
                "risk_level": risk
            }
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

    def predict_bulk(self, df):
        if not self.pipeline:
            if not self.load_model():
                return None, "No trained model is available. Please upload a dataset containing both Churn=Yes and Churn=No records."

        try:
            # Keep original for returning
            orig_df = df.copy()

            expected_num_cols = self.pipeline.named_steps['preprocessor'].transformers_[0][2]
            expected_cat_cols = self.pipeline.named_steps['preprocessor'].transformers_[1][2]

            for col in expected_num_cols:
                if col not in orig_df.columns:
                    orig_df[col] = 0.0
            for col in expected_cat_cols:
                if col not in orig_df.columns:
                    orig_df[col] = 'Unknown'

            if 'total_charges' in orig_df.columns:
                orig_df['total_charges'] = pd.to_numeric(orig_df['total_charges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')

            cat_cols = orig_df.select_dtypes(include=['object']).columns.tolist()
            num_cols = orig_df.select_dtypes(include=['int64', 'float64']).columns.tolist()

            for col in num_cols:
                orig_df[col] = orig_df[col].fillna(0.0)
            for col in cat_cols:
                orig_df[col] = orig_df[col].fillna('Unknown')

            all_features = expected_num_cols + expected_cat_cols
            X = orig_df[all_features]

            if hasattr(self.pipeline, "predict_proba"):
                probs = self.pipeline.predict_proba(X)[:, 1]
            else:
                probs = self.pipeline.predict(X)

            orig_df['churn_probability'] = np.round(probs * 100, 1)
            orig_df['predicted_churn'] = ['Yes' if p > 0.5 else 'No' for p in probs]

            def get_risk(p):
                if p >= 0.7: return "High"
                if p >= 0.4: return "Medium"
                return "Low"

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
