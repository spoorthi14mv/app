from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db
from models.customer import Customer
from models.prediction import Prediction

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    filter_risk = request.args.get('risk', '')
    filter_contract = request.args.get('contract', '')
    filter_internet = request.args.get('internet_service', '')
    filter_churn = request.args.get('churn', '')

    # Outer join to get ALL customers, regardless of prediction
    query = db.session.query(Customer, Prediction).outerjoin(
        Prediction, Customer.customer_id == Prediction.customer_id
    )

    if search:
        # Case insensitive like search
        query = query.filter(Customer.customer_id.ilike(f'%{search}%'))

    if filter_risk and filter_risk.lower() != 'all':
        query = query.filter(Prediction.risk_level == filter_risk.capitalize())

    if filter_contract and filter_contract.lower() != 'all':
        query = query.filter(Customer.contract == filter_contract)

    if filter_internet and filter_internet.lower() != 'all':
        query = query.filter(Customer.internet_service == filter_internet)

    if filter_churn and filter_churn.lower() != 'all':
        query = query.filter(Customer.churn == filter_churn)

    # Sort by prediction churn descending if possible, then ID
    query = query.order_by(Prediction.churn_probability.desc().nullslast(), Customer.customer_id.asc())

    pagination = query.paginate(page=page, per_page=25, error_out=False)

    return render_template('customers.html',
                           pagination=pagination,
                           search=search,
                           filter_risk=filter_risk,
                           filter_contract=filter_contract,
                           filter_internet=filter_internet,
                           filter_churn=filter_churn)

@customer_bp.route('/customers/new', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()
        if not customer_id:
            flash('Customer ID is required.', 'danger')
            return redirect(url_for('customer.create'))

        existing = Customer.query.filter_by(customer_id=customer_id).first()
        if existing:
            flash('Customer ID already exists.', 'danger')
            return redirect(url_for('customer.create'))

        try:
            customer = Customer(
                customer_id=customer_id,
                gender=request.form.get('gender', 'Unknown'),
                senior_citizen=int(request.form.get('senior_citizen', 0)),
                partner=request.form.get('partner', 'No'),
                dependents=request.form.get('dependents', 'No'),
                tenure=int(request.form.get('tenure', 0)),
                phone_service=request.form.get('phone_service', 'No'),
                multiple_lines=request.form.get('multiple_lines', 'No phone service'),
                internet_service=request.form.get('internet_service', 'No'),
                online_security=request.form.get('online_security', 'No internet service'),
                online_backup=request.form.get('online_backup', 'No internet service'),
                device_protection=request.form.get('device_protection', 'No internet service'),
                tech_support=request.form.get('tech_support', 'No internet service'),
                streaming_tv=request.form.get('streaming_tv', 'No internet service'),
                streaming_movies=request.form.get('streaming_movies', 'No internet service'),
                contract=request.form.get('contract', 'Month-to-month'),
                paperless_billing=request.form.get('paperless_billing', 'Yes'),
                payment_method=request.form.get('payment_method', 'Electronic check'),
                monthly_charges=float(request.form.get('monthly_charges', 0.0)),
                total_charges=float(request.form.get('total_charges', 0.0)),
                churn=request.form.get('churn', 'No')
            )
            db.session.add(customer)
            db.session.commit()
            flash('Customer created successfully.', 'success')
            return redirect(url_for('customer.index'))
        except Exception as e:
            db.session.rollback()
            flash('Unable to save customer. Please try again.', 'danger')

    return render_template('customer_form.html', customer=None)

@customer_bp.route('/customers/<customer_id>')
def details(customer_id):
    customer = Customer.query.filter_by(customer_id=customer_id).first()
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customer.index'))

    prediction = Prediction.query.filter_by(customer_id=customer_id).first()
    return render_template('customer_detail.html', customer=customer, prediction=prediction)

@customer_bp.route('/customers/<customer_id>/edit', methods=['GET', 'POST'])
def update(customer_id):
    customer = Customer.query.filter_by(customer_id=customer_id).first()
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customer.index'))

    if request.method == 'POST':
        try:
            customer.gender = request.form.get('gender', 'Unknown')
            customer.senior_citizen = int(request.form.get('senior_citizen', 0))
            customer.partner = request.form.get('partner', 'No')
            customer.dependents = request.form.get('dependents', 'No')
            customer.tenure = int(request.form.get('tenure', 0))
            customer.phone_service = request.form.get('phone_service', 'No')
            customer.multiple_lines = request.form.get('multiple_lines', 'No phone service')
            customer.internet_service = request.form.get('internet_service', 'No')
            customer.online_security = request.form.get('online_security', 'No internet service')
            customer.online_backup = request.form.get('online_backup', 'No internet service')
            customer.device_protection = request.form.get('device_protection', 'No internet service')
            customer.tech_support = request.form.get('tech_support', 'No internet service')
            customer.streaming_tv = request.form.get('streaming_tv', 'No internet service')
            customer.streaming_movies = request.form.get('streaming_movies', 'No internet service')
            customer.contract = request.form.get('contract', 'Month-to-month')
            customer.paperless_billing = request.form.get('paperless_billing', 'Yes')
            customer.payment_method = request.form.get('payment_method', 'Electronic check')
            customer.monthly_charges = float(request.form.get('monthly_charges', 0.0))
            customer.total_charges = float(request.form.get('total_charges', 0.0))
            customer.churn = request.form.get('churn', 'No')

            db.session.commit()
            flash('Customer updated successfully.', 'success')
            return redirect(url_for('customer.details', customer_id=customer_id))
        except Exception as e:
            db.session.rollback()
            flash('Unable to save customer. Please try again.', 'danger')

    return render_template('customer_form.html', customer=customer)

@customer_bp.route('/customers/<customer_id>/delete', methods=['POST'])
def delete(customer_id):
    customer = Customer.query.filter_by(customer_id=customer_id).first()
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customer.index'))

    try:
        Prediction.query.filter_by(customer_id=customer_id).delete()
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Unable to delete customer.', 'danger')

    return redirect(url_for('customer.index'))
