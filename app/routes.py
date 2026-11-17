from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import db, login_manager
from .models import User, SHGProfile, YouthProfile, EmployerProfile, Order, WorkforceRequest, Application
from .forms import LoginForm, RegisterForm, OrderForm, ApplicationForm
from .matcher import find_matching_youth

main_bp = Blueprint('main', __name__)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('main.login'))

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id before committing
        # Create role‑specific profile
        if user.role == 'shg':
            profile = SHGProfile(name=form.name.data, description=form.description.data,
                                 location=form.location.data, user_id=user.id)
        elif user.role == 'youth':
            profile = YouthProfile(full_name=form.name.data, skills=form.skills.data,
                                   availability=form.availability.data, location=form.location.data,
                                   user_id=user.id)
        elif user.role == 'employer':
            profile = EmployerProfile(company_name=form.name.data, contact_person=form.contact_person.data,
                                      location=form.location.data, user_id=user.id)
        else:
            profile = None
        if profile:
            db.session.add(profile)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'shg':
        return redirect(url_for('main.shg_dashboard'))
    elif current_user.role == 'youth':
        return redirect(url_for('main.youth_dashboard'))
    elif current_user.role == 'employer':
        return redirect(url_for('main.employer_dashboard'))
    else:
        flash('Unknown role.', 'danger')
        return redirect(url_for('main.index'))

# ---------- SHG Views ----------

@main_bp.route('/shg')
@login_required
def shg_dashboard():
    if current_user.role != 'shg':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    shg = current_user.shg_profile
    orders = shg.orders if shg else []
    return render_template('dashboard_shg.html', shg=shg, orders=orders)

@main_bp.route('/shg/order/create', methods=['GET', 'POST'])
@login_required
def create_order():
    if current_user.role != 'shg':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    form = OrderForm()
    if form.validate_on_submit():
        order = Order(
            title=form.title.data,
            description=form.description.data,
            quantity=form.quantity.data,
            deadline=form.deadline.data,
            shg_id=current_user.shg_profile.id,
        )
        db.session.add(order)
        db.session.commit()
        flash('Order created.', 'success')
        return redirect(url_for('main.shg_dashboard'))
    return render_template('create_order.html', form=form)

@main_bp.route('/shg/order/<int:order_id>')
@login_required
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.role != 'shg' or order.shg_id != current_user.shg_profile.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.shg_dashboard'))
    # No auto‑generation of workforce requests – SHGs should use the explicit form.
    return render_template('view_order.html', order=order)

# New view: create a detailed workforce request for an order
@main_bp.route('/shg/order/<int:order_id>/request/create', methods=['GET', 'POST'])
@login_required
def create_workforce_request(order_id):
    if current_user.role != 'shg':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    order = Order.query.get_or_404(order_id)
    if order.shg_id != current_user.shg_profile.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.shg_dashboard'))
    from .forms import WorkforceRequestForm
    form = WorkforceRequestForm()
    if form.validate_on_submit():
        req = WorkforceRequest(
            job_title=form.job_title.data,
            required_skills=form.required_skills.data,
            needed_quantity=form.needed_quantity.data,
            location=form.location.data,
            payment_amount=float(form.payment_amount.data) if form.payment_amount.data else None,
            duration_days=form.duration_days.data,
            description=form.description.data,
            order_id=order.id,
        )
        db.session.add(req)
        db.session.commit()
        flash('Workforce request created.', 'success')
        return redirect(url_for('main.view_workforce_request', req_id=req.id))
    return render_template('create_workforce_request.html', form=form, order=order)

# View applications for a workforce request and allow SHG to accept/reject
@main_bp.route('/shg/request/<int:req_id>/applications', methods=['GET', 'POST'])
@login_required
def view_applications(req_id):
    """Display applications for a request and process accept/reject actions.
    Only the SHG who owns the related order can access this view.
    """
    if current_user.role != 'shg':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    req = WorkforceRequest.query.get_or_404(req_id)
    if not req.order or req.order.shg_id != current_user.shg_profile.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.shg_dashboard'))
    if request.method == 'POST':
        app_id = request.form.get('app_id')
        action = request.form.get('action')
        application = Application.query.filter_by(id=app_id, request_id=req_id).first()
        if not application:
            flash('Application not found.', 'danger')
        elif application.status != 'pending':
            flash(f'Application already {application.status}.', 'warning')
        elif action in ('accept', 'reject'):
            application.status = 'accepted' if action == 'accept' else 'rejected'
            db.session.commit()
            flash(f'Application {action}ed.', 'success')
        else:
            flash('Invalid action.', 'danger')
        return redirect(url_for('main.view_applications', req_id=req_id))
    # GET – render list
    return render_template('view_applications.html', request=req, applications=req.applications)

# Display details of a single WorkforceRequest
@main_bp.route('/shg/request/<int:req_id>')
@login_required
def view_workforce_request(req_id):
    """Display details of a single WorkforceRequest.
    Only accessible by the SHG that owns the related order.
    """
    if current_user.role != 'shg':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    req = WorkforceRequest.query.get_or_404(req_id)
    if not req.order or req.order.shg_id != current_user.shg_profile.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.shg_dashboard'))
    return render_template('view_workforce_request.html', request=req)

# ---------- Youth Views ----------
@main_bp.route('/youth')
@login_required
def youth_dashboard():
    if current_user.role != 'youth':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    youth = current_user.youth_profile
    # Show all open workforce requests for youth discovery
    open_requests = WorkforceRequest.query.filter_by(status='open').all()
    return render_template('dashboard_youth.html', youth=youth, requests=open_requests)

@main_bp.route('/youth/request/<int:req_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_to_request(req_id):
    if current_user.role != 'youth':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    # Ensure youth profile exists
    youth_profile = current_user.youth_profile
    if not youth_profile:
        flash('Youth profile not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    request_obj = WorkforceRequest.query.get_or_404(req_id)
    # Prevent applications to closed requests
    if request_obj.status != 'open':
        flash('Cannot apply to a closed request.', 'warning')
        return redirect(url_for('main.youth_dashboard'))
    # Process application directly on GET (no separate form needed)
    # Check for duplicate application
    existing = Application.query.filter_by(request_id=req_id, youth_id=youth_profile.id).first()
    if existing:
        flash('You have already applied.', 'info')
    else:
        app_entry = Application(request_id=req_id, youth_id=youth_profile.id)
        db.session.add(app_entry)
        db.session.commit()
        flash('Application submitted.', 'success')
    return redirect(url_for('main.youth_dashboard'))


# ---------- Employer Views ----------
@main_bp.route('/employer')
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    employer = current_user.employer_profile
    orders = employer.orders if employer else []
    return render_template('dashboard_employer.html', employer=employer, orders=orders)
