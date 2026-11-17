import os, sys
sys.path.append(os.getcwd())
from app import create_app, db
from app.models import User, YouthProfile, SHGProfile, Order, WorkforceRequest, Application

app = create_app()
app.app_context().push()
# Ensure DB has at least one youth and one open request
# Find or create a youth user
youth = User.query.filter_by(email='youth@example.com').first()
if not youth:
    youth = User(email='youth@example.com', role='youth')
    youth.set_password('password')
    db.session.add(youth)
    db.session.flush()
    youth_profile = YouthProfile(full_name='Test Youth', skills='stitching, embroidery', availability='full-time', location='Test City', user_id=youth.id)
    db.session.add(youth_profile)
    db.session.commit()
else:
    youth_profile = youth.youth_profile
# Create a SHG and order if needed
shg_user = User.query.filter_by(email='shg@example.com').first()
if not shg_user:
    shg_user = User(email='shg@example.com', role='shg')
    shg_user.set_password('password')
    db.session.add(shg_user)
    db.session.flush()
    shg_profile = SHGProfile(name='Test SHG', description='desc', location='Test City', user_id=shg_user.id)
    db.session.add(shg_profile)
    db.session.commit()
else:
    shg_profile = shg_user.shg_profile
order = Order.query.filter_by(title='Test Order').first()
if not order:
    order = Order(title='Test Order', description='desc', quantity=10, deadline='2030-01-01 00:00', shg_id=shg_profile.id)
    db.session.add(order)
    db.session.commit()
# Create an open workforce request if none
req = WorkforceRequest.query.filter_by(job_title='Test Job').first()
if not req:
    req = WorkforceRequest(job_title='Test Job', required_skills='stitching', needed_quantity=5, location='Test City', payment_amount=1000.0, duration_days=30, description='test', order_id=order.id, status='open')
    db.session.add(req)
    db.session.commit()

client = app.test_client()
# Login as youth
login_resp = client.post('/login', data={'email': 'youth@example.com', 'password': 'password'}, follow_redirects=True)
print('Login status code', login_resp.status_code)
# Access youth dashboard
dash_resp = client.get('/youth')
print('Dashboard contains request id', str(req.id) in dash_resp.get_data(as_text=True))
# Apply to request
apply_resp = client.post(f'/youth/request/{req.id}/apply', follow_redirects=True)
print('Apply status code', apply_resp.status_code)
# Check application exists
app_entry = Application.query.filter_by(request_id=req.id, youth_id=youth_profile.id).first()
print('Application exists', bool(app_entry))
