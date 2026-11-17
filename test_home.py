import sys, os
sys.path.append('app')
from app import create_app
app = create_app()
with app.test_client() as client:
    resp = client.get('/')
    print('status', resp.status_code)
    print('length', len(resp.data))
    print(resp.data[:200].decode('utf-8', errors='replace'))
