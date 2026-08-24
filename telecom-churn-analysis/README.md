# Telecom Churn Analysis: From Raw Data to Actionable Business Insights

## Project Description
A complete, professional Telecom Customer Churn Analysis and Prediction System. This application provides a modern dashboard UI to upload raw telecom customer data, perform automated data cleaning, visually analyze churn factors, train machine learning models to predict churn risk, and automatically generate actionable business recommendations based on the findings.

## Features
- **Data Upload & Preprocessing:** Upload CSV/Excel datasets and automatically clean them.
- **Data Exploration:** Filter and search through processed customer records.
- **Churn Analysis Dashboard:** Interactive Chart.js visualizations showing churn distribution by various features.
- **Machine Learning Integration:** Train and compare Logistic Regression, Decision Tree, Random Forest, and XGBoost models to predict churn probability.
- **Customer Prediction:** Predict risk for individual customers or run bulk predictions via file upload.
- **Risk Segmentation:** Group customers into strategic segments (e.g., High Value - High Risk).
- **Business Insights:** Generate dynamic recommendations for high-risk customers based on their characteristics.
- **Reports:** View model metrics and export high-risk customers to Excel.
- **Modern UI:** Responsive design with light/dark mode support.

## Objectives
This project aims to demonstrate an end-to-end data science lifecycle applied to a realistic business problem, moving from raw data ingestion to generating tangible business value.

## Technologies
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js, Font Awesome
- **Backend:** Python 3.x, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Data Science / ML:** Pandas, NumPy, Scikit-learn, XGBoost, Joblib
- **Database:** SQLite (default), optionally MySQL (via SQLAlchemy configuration)

## Architecture
The application uses a modular, Flask blueprint-based architecture with separate layers for routing, database models, and business logic services.
- `app.py`: Application factory
- `config.py`: Environment configuration
- `extensions.py`: Flask extensions
- `models/`: Database models using SQLAlchemy
- `routes/`: Flask blueprints for web endpoints
- `services/`: Business logic for ML training, data cleaning, and analysis
- `templates/` & `static/`: Frontend files

## Installation

### Virtual Environment Setup
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

### Dependencies
Install the required packages:
`pip install -r requirements.txt`

### Database Setup
The application uses SQLite by default. To initialize the database and create the default admin account, run:
`python -m flask --app app init-db`
This will create a `telecom_churn.db` file in the `instance/` folder and generate an admin user with credentials:
- **Username:** admin (or admin@telecom.com)
- **Password:** admin123

To use MySQL, set the `DATABASE_URL` environment variable:
`export DATABASE_URL=mysql+pymysql://username:password@localhost/telecom_churn`

## How to Run
Start the development server:
`python app.py`
Access the application at `http://127.0.0.1:5000/`

## Excel Dataset Format
The application expects a standard telecom churn dataset structure (e.g., Telco Customer Churn) with columns such as:
`customerID, gender, SeniorCitizen, Partner, Dependents, tenure, PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges, Churn`.

Minor variations in column names (e.g., `customer_id` vs `customerID`) are normalized automatically during upload. A script (`generate_data.py`) is provided in the repository to generate a sample Excel file.

## Machine Learning Workflow
1. Upload a dataset in the **Data Upload** page.
2. Navigate to the **Prediction** page.
3. Click **Train/Update Model**.
4. The system automatically handles numeric scaling, categorical encoding, and trains multiple classifiers.
5. The model with the best F1/ROC-AUC score is selected and saved via Joblib in the `ml_models/` directory.
6. The system uses this saved model for all subsequent individual or bulk predictions.

## API Information
The system provides several internal API endpoints returning JSON data for the frontend dashboards:
- `/api/dashboard/charts`: Returns chart configuration data based on the current database state.
- `/predict` (POST): Accepts individual customer data and returns a churn risk probability.
- `/bulk-predict` (POST): Processes uploaded files and generates predictions.
- `/train` (POST): Initiates model training on the currently loaded dataset.
