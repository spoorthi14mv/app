import pandas as pd
import numpy as np
from models import db
from models.customer import Customer

class DataProcessor:
    @staticmethod
    def process_file(filepath):
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            else:
                return None, "Unsupported file format"

            # Normalize column names for consistency
            column_mapping = {
                'customerid': 'customer_id',
                'customer_id': 'customer_id',
                'gender': 'gender',
                'seniorcitizen': 'senior_citizen',
                'senior_citizen': 'senior_citizen',
                'partner': 'partner',
                'dependents': 'dependents',
                'tenure': 'tenure',
                'phoneservice': 'phone_service',
                'phone_service': 'phone_service',
                'multiplelines': 'multiple_lines',
                'multiple_lines': 'multiple_lines',
                'internetservice': 'internet_service',
                'internet_service': 'internet_service',
                'onlinesecurity': 'online_security',
                'online_security': 'online_security',
                'onlinebackup': 'online_backup',
                'online_backup': 'online_backup',
                'deviceprotection': 'device_protection',
                'device_protection': 'device_protection',
                'techsupport': 'tech_support',
                'tech_support': 'tech_support',
                'streamingtv': 'streaming_tv',
                'streaming_tv': 'streaming_tv',
                'streamingmovies': 'streaming_movies',
                'streaming_movies': 'streaming_movies',
                'contract': 'contract',
                'paperlessbilling': 'paperless_billing',
                'paperless_billing': 'paperless_billing',
                'paymentmethod': 'payment_method',
                'payment_method': 'payment_method',
                'monthlycharges': 'monthly_charges',
                'monthly_charges': 'monthly_charges',
                'totalcharges': 'total_charges',
                'total_charges': 'total_charges',
                'churn': 'churn'
            }

            df.columns = [str(c).lower().strip() for c in df.columns]
            df.rename(columns=lambda x: column_mapping.get(x, x), inplace=True)

            required_columns = ['customer_id', 'tenure', 'monthly_charges', 'churn']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                return None, f"Missing required columns: {', '.join(missing_cols)}"

            # Basic Cleaning
            initial_records = len(df)

            # Remove duplicates
            df.drop_duplicates(inplace=True)
            duplicates_removed = initial_records - len(df)

            # Handle TotalCharges if present
            if 'total_charges' in df.columns:
                df['total_charges'] = pd.to_numeric(df['total_charges'].replace(' ', np.nan), errors='coerce')
                # Fill missing total charges based on tenure and monthly charges
                df['total_charges'] = df['total_charges'].fillna(df['tenure'] * df['monthly_charges'])

            # Fill missing numerical with median, categorical with mode
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df[col] = df[col].fillna(df[col].mode()[0])

            missing_values_handled = True # Simplification for reporting

            # Store in DB
            db.session.query(Customer).delete() # clear existing
            db.session.commit()

            customers = []
            for _, row in df.iterrows():
                customer = Customer(
                    customer_id=str(row.get('customer_id')),
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
                customers.append(customer)

            db.session.bulk_save_objects(customers)
            db.session.commit()

            summary = {
                'rows': len(df),
                'columns': len(df.columns),
                'duplicates_removed': duplicates_removed,
                'missing_values_handled': missing_values_handled
            }

            return df, summary

        except Exception as e:
            db.session.rollback()
            return None, str(e)
