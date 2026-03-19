import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebApp.settings')
django.setup()

from django.test import Client

client = Client()

session = client.session
session['user_id'] = 'NV001'
session['user_name'] = 'Admin Test'
session['user_role'] = 'Admin'
session.save()

urls_to_test = [
    '/stores/', '/stores/add/', 
    '/warehouses/', '/warehouses/add/',
    '/products/', '/products/add/',
    '/categories/', '/categories/add/',
    '/employees/', '/employees/add/',
    '/stock-in/', '/stock-in/add/',
    '/inventory/', '/inventory/add/'
]

errors = []
print("Testing GET requests for List and Add views...")
for url in urls_to_test:
    response = client.get(url)
    if response.status_code != 200:
        errors.append(f"FAIL: GET {url} returned {response.status_code} ({response.content[:100]})")
    else:
        print(f"OK: GET {url}")

if errors:
    print("\n--- ERRORS FOUND ---")
    for e in errors:
        print(e)
else:
    print("\n--- All GET requests successful! ---")
