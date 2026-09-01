import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from models import db
from models.customer import Customer
from models.dataset import Dataset
from services.data_processor import DataProcessor

data_bp = Blueprint('data', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@data_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            df, summary = DataProcessor.process_file(filepath)

            if df is not None:
                # Save dataset info
                dataset = Dataset(
                    filename=filename,
                    records=summary['rows'],
                    columns=summary['columns']
                )
                db.session.add(dataset)
                db.session.commit()

                # Auto-train model after upload
                from services.model_trainer import ModelTrainer
                customers = Customer.query.all()
                if len(customers) > 0:
                    data_list = []
                    for c in customers:
                        data_list.append({
                            'customer_id': c.customer_id,
                            'gender': c.gender,
                            'senior_citizen': c.senior_citizen,
                            'partner': c.partner,
                            'dependents': c.dependents,
                            'tenure': c.tenure,
                            'phone_service': c.phone_service,
                            'multiple_lines': c.multiple_lines,
                            'internet_service': c.internet_service,
                            'online_security': c.online_security,
                            'online_backup': c.online_backup,
                            'device_protection': c.device_protection,
                            'tech_support': c.tech_support,
                            'streaming_tv': c.streaming_tv,
                            'streaming_movies': c.streaming_movies,
                            'contract': c.contract,
                            'paperless_billing': c.paperless_billing,
                            'payment_method': c.payment_method,
                            'monthly_charges': c.monthly_charges,
                            'total_charges': c.total_charges,
                            'churn': c.churn
                        })
                    train_df = pd.DataFrame(data_list)
                    trainer = ModelTrainer()
                    result = trainer.train_and_evaluate(train_df)
                    if "error" in result:
                        flash(f'Data uploaded, but model training failed: {result["error"]}', 'warning')
                    else:
                        flash(f'File successfully uploaded. Model automatically trained: {result["best_model"]}', 'success')
                else:
                    flash(f'File successfully uploaded, but no records were valid for training.', 'warning')

                return render_template('upload.html', summary=summary, filename=filename)
            else:
                flash(f'Error processing file: {summary}', 'danger')

    return render_template('upload.html')
