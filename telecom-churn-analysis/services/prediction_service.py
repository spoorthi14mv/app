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

            # Upsert customers and predictions
            from models.customer import Customer

            customer_ids = [str(cid) for cid in orig_df['customer_id'].tolist()]

            # Fetch existing customers and predictions
            existing_customers = {c.customer_id: c for c in Customer.query.filter(Customer.customer_id.in_(customer_ids)).all()}
            existing_predictions = {p.customer_id: p for p in Prediction.query.filter(Prediction.customer_id.in_(customer_ids)).all()}

            new_customers = []
            new_predictions = []

            for i, row in orig_df.iterrows():
                cid = str(row['customer_id'])

                # Upsert Customer if it's a new file (columns might be present)
                if cid not in existing_customers:
                    # We might not have all columns if it's purely a prediction payload,
                    # but if we do, we save them. Otherwise defaults.
                    cust = Customer(
                        customer_id=cid,
                        gender=str(row.get('gender', 'Unknown')),
                        senior_citizen=int(row.get('senior_citizen', 0)),
                        partner=str(row.get('partner', 'No')),
                        dependents=str(row.get('dependents', 'No')),
                        tenure=int(row.get('tenure', 0)),
                        phone_service=str(row.get('phone_service', 'No')),
                        multiple_lines=str(row.get('multiple_lines', 'No phone service')),
                        internet_service=str(row.get('internet_service', 'No')),
                        online_security=str(row.get('online_security', 'No internet service')),
                        online_backup=str(row.get('online_backup', 'No internet service')),
                        device_protection=str(row.get('device_protection', 'No internet service')),
                        tech_support=str(row.get('tech_support', 'No internet service')),
                        streaming_tv=str(row.get('streaming_tv', 'No internet service')),
                        streaming_movies=str(row.get('streaming_movies', 'No internet service')),
                        contract=str(row.get('contract', 'Month-to-month')),
                        paperless_billing=str(row.get('paperless_billing', 'Yes')),
                        payment_method=str(row.get('payment_method', 'Electronic check')),
                        monthly_charges=float(row.get('monthly_charges', 0.0)),
                        total_charges=float(row.get('total_charges', 0.0)),
                        churn=str(row.get('churn', 'No'))
                    )
                    new_customers.append(cust)

                # Upsert Prediction
                prob = float(row['churn_probability'])
                pred_val = str(row['predicted_churn'])
                risk = str(row['risk_level'])

                if cid in existing_predictions:
                    pred = existing_predictions[cid]
                    pred.churn_probability = prob
                    pred.predicted_churn = pred_val
                    pred.risk_level = risk
                else:
                    pred = Prediction(
                        customer_id=cid,
                        churn_probability=prob,
                        predicted_churn=pred_val,
                        risk_level=risk,
                        model_name="Selected Model"
                    )
                    new_predictions.append(pred)

            if new_customers:
                db.session.bulk_save_objects(new_customers)
            if new_predictions:
                db.session.bulk_save_objects(new_predictions)

            db.session.commit()

            return orig_df, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)
