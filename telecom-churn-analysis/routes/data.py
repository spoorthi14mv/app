import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
from models import db
from models.customer import Customer
from models.dataset import Dataset
from services.data_processor import DataProcessor

data_bp = Blueprint('data', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@data_bp.route('/upload', methods=['GET', 'POST'])
@login_required
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

                flash(f'File successfully uploaded and processed. Cleaned records: {len(df)}', 'success')
                return render_template('upload.html', summary=summary, filename=filename)
            else:
                flash(f'Error processing file: {summary}', 'danger')

    return render_template('upload.html')

@data_bp.route('/data')
@login_required
def explorer():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Customer.query
    if search:
        query = query.filter(Customer.customer_id.contains(search))

    pagination = query.paginate(page=page, per_page=50, error_out=False)
    customers = pagination.items

    return render_template('data.html', customers=customers, pagination=pagination, search=search)
