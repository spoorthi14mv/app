import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
from models import db
from models.model_result import ModelResult
from flask import current_app

class ModelTrainer:
    def __init__(self):
        self.models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
            'Random Forest': RandomForestClassifier(random_state=42)
        }
        if XGB_AVAILABLE:
            self.models['XGBoost'] = xgb.XGBClassifier(random_state=42, eval_metric='logloss')

    def preprocess_data(self, df):
        # Prepare for ML
        # Drop columns not useful for prediction
        drop_cols = ['customer_id', 'created_at']
        for col in drop_cols:
            if col in df.columns:
                df = df.drop(col, axis=1)

        # Handle Target
        if 'churn' not in df.columns:
            raise ValueError("Target variable 'churn' not found.")

        y = df['churn'].map({'Yes': 1, 'No': 0, '1': 1, '0': 0})
        X = df.drop('churn', axis=1)

        # Separate categorical and numerical features
        cat_cols = X.select_dtypes(include=['object']).columns
        num_cols = X.select_dtypes(include=['int64', 'float64']).columns

        # Encoders and Scalers
        encoders = {}
        for col in cat_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le

        scaler = StandardScaler()
        if len(num_cols) > 0:
            X[num_cols] = scaler.fit_transform(X[num_cols])

        pipeline = {
            'encoders': encoders,
            'scaler': scaler,
            'cat_cols': cat_cols,
            'num_cols': num_cols,
            'features': X.columns.tolist()
        }

        return X, y, pipeline

    def train_and_evaluate(self, df):
        X, y, pipeline = self.preprocess_data(df.copy())

        # Check if we have valid classes
        if len(y.unique()) < 2:
            return {"error": "Dataset needs both 'Yes' and 'No' in Churn column to train models."}

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        results = []
        best_model_name = None
        best_f1 = -1
        best_model_obj = None

        db.session.query(ModelResult).delete()

        for name, model in self.models.items():
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            if hasattr(model, "predict_proba"):
                y_prob = model.predict_proba(X_test)[:, 1]
                roc_auc = roc_auc_score(y_test, y_prob)
            else:
                roc_auc = 0.0

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)

            mr = ModelResult(
                model_name=name,
                accuracy=acc,
                precision=prec,
                recall=rec,
                f1_score=f1,
                roc_auc=roc_auc
            )
            db.session.add(mr)

            results.append({
                'model_name': name,
                'accuracy': acc,
                'precision': prec,
                'recall': rec,
                'f1_score': f1,
                'roc_auc': roc_auc
            })

            # Select best model based on F1 Score or ROC-AUC
            if f1 > best_f1:
                best_f1 = f1
                best_model_name = name
                best_model_obj = model

        db.session.commit()

        # Save best model and pipeline
        models_dir = current_app.config['MODELS_DIR']
        joblib.dump(best_model_obj, os.path.join(models_dir, 'model.joblib'))
        joblib.dump(pipeline, os.path.join(models_dir, 'preprocessing.joblib'))

        return {
            'results': results,
            'best_model': best_model_name
        }
