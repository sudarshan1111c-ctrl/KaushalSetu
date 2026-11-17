import sys, traceback
from app import create_app, db
from app.models import User, SHGProfile, YouthProfile, Order, WorkforceRequest, Application


def run_test():
    app = create_app()
    app.testing = True
    client = app.test_client()
    with app.app_context():
        # Clean up any existing test users (by email) to avoid duplicates
        for email in ['shg_test@example.com', 'youth_test@example.com']:
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
        db.session.commit()
        # Create SHG user
        shg_user = User(email='shg_test@example.com', role='shg')
        shg_user.set_password('password')
        db.session.add(shg_user)
        db.session.flush()
        shg_profile = SHGProfile(name='Test SHG', description='Test', location='Village', user_id=shg_user.id)
        db.session.add(shg_profile)
        db.session.flush()
        # Create Youth user
        youth_user = User(email='youth_test@example.com', role='youth')
        youth_user.set_password('password')
        db.session.add(youth_user)
        db.session.flush()
        youth_profile = YouthProfile(full_name='Test Youth', skills='stitching, embroidery', availability='fulltime', location='Town', user_id=youth_user.id)
        db.session.add(youth_profile)
        db.session.flush()
        # Create Order for SHG
        order = Order(title='Test Order', description='Desc', quantity=100, deadline='2030-01-01 00:00', shg_id=shg_profile.id)
        db.session.add(order)
        db.session.flush()
        # Create Workforce Request via direct model (full fields)
        req = WorkforceRequest(
            job_title='Test Job',
            required_skills='stitching, embroidery',
            needed_quantity=10,
            location='Town',
            payment_amount=5000.0,
            duration_days=30,
            description='Help needed',
            order_id=order.id,
        )
        db.session.add(req)
        db.session.flush()
        # Verify request saved
        assert req.id is not None, 'Request not saved'
        # Youth login and apply
        login_resp = client.post('/login', data={'email': 'youth_test@example.com', 'password': 'password'}, follow_redirects=True)
        assert b'Logged in successfully' in login_resp.data, 'Youth login failed'
        apply_resp = client.post(f'/youth/request/{req.id}/apply', follow_redirects=True)
        assert b'Application submitted' in apply_resp.data or b'You have already applied' in apply_resp.data, 'Youth apply failed'
        # Verify application exists
        application = Application.query.filter_by(request_id=req.id, youth_id=youth_profile.id).first()
        assert application is not None, 'Application not created'
        # Logout youth
        client.get('/logout', follow_redirects=True)
        # SHG login
        login_resp = client.post('/login', data={'email': 'shg_test@example.com', 'password': 'password'}, follow_redirects=True)
        assert b'Logged in successfully' in login_resp.data, 'SHG login failed'
        # View applications page GET
        apps_page = client.get(f'/shg/request/{req.id}/applications')
        assert b'Test Youth' in apps_page.data, 'Applications page does not list youth'
        # Accept application via POST
        accept_resp = client.post(f'/shg/request/{req.id}/applications', data={'app_id': application.id, 'action': 'accept'}, follow_redirects=True)
        assert b'Application accepted' in accept_resp.data, 'Accept action failed'
        # Verify status changed
        db.session.refresh(application)
        assert application.status == 'accepted', f'Status not updated, got {application.status}'
        # Cleanup test data
        db.session.delete(application)
        db.session.delete(req)
        db.session.delete(order)
        db.session.delete(shg_profile)
        db.session.delete(shg_user)
        db.session.delete(youth_profile)
        db.session.delete(youth_user)
        db.session.commit()
        print('END_TO_END_TEST_SUCCESS')

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
