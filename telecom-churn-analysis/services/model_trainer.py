import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from models import db
from models.model_result import ModelResult
from flask import current_app

class ModelTrainer:
    def __init__(self):
        # We only need one or two good models.
        self.models = {
            'Random Forest': RandomForestClassifier(random_state=42),
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42)
        }

    def train_and_evaluate(self, df):
        # Check target
        if 'churn' not in df.columns:
            return {"error": "Target variable 'Churn' not found."}

        # Check target classes
        y = df['churn'].map({'Yes': 1, 'No': 0, '1': 1, '0': 0})
        if len(y.dropna().unique()) < 2:
            return {"error": "Model training requires both Churn=Yes and Churn=No records. Please upload a dataset containing both classes."}

        # Prepare X and handle blanks safely
        X = df.drop('churn', axis=1)

        # Drop columns not useful for prediction
        drop_cols = ['customer_id', 'created_at']
        for col in drop_cols:
            if col in X.columns:
                X = X.drop(col, axis=1)

        # Ensure TotalCharges is numeric, coercing blanks to NaN, then fill
        if 'total_charges' in X.columns:
            X['total_charges'] = pd.to_numeric(X['total_charges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')

        # Separate categorical and numerical features
        cat_cols = X.select_dtypes(include=['object']).columns.tolist()
        num_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

        # Preprocessing pipeline
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, num_cols),
                ('cat', categorical_transformer, cat_cols)
            ])

        # Fill missing values simply before pipeline
        for col in num_cols:
            X[col] = X[col].fillna(0)
        for col in cat_cols:
            X[col] = X[col].fillna('Unknown')

        # Split Data
        # Ensure we only use non-null y
        valid_idx = y.dropna().index
        X = X.loc[valid_idx]
        y = y.loc[valid_idx]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        results = []
        best_model_name = None
        best_f1 = -1
        best_pipeline = None

        db.session.query(ModelResult).delete()

        for name, classifier in self.models.items():
            clf = Pipeline(steps=[('preprocessor', preprocessor),
                                  ('classifier', classifier)])

            try:
                clf.fit(X_train, y_train)

                y_pred = clf.predict(X_test)
                if hasattr(classifier, "predict_proba"):
                    y_prob = clf.predict_proba(X_test)[:, 1]
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

                # Select best model based on F1 Score
                if f1 > best_f1:
                    best_f1 = f1
                    best_model_name = name
                    best_pipeline = clf
            except Exception as e:
                print(f"Error training {name}: {str(e)}")

        db.session.commit()

        if best_pipeline is None:
             return {"error": "Failed to train models."}

        # Save best model pipeline
        models_dir = current_app.config['MODELS_DIR']
        joblib.dump(best_pipeline, os.path.join(models_dir, 'pipeline.joblib'))

        return {
            'results': results,
            'best_model': best_model_name
        }
