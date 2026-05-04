import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebApp.settings')
django.setup()

from django.db import connection

sql = "ALTER TABLE donhang ADD COLUMN pt_thanhtoan VARCHAR(50) DEFAULT 'COD';"

with connection.cursor() as cursor:
    try:
        cursor.execute(sql)
        print("SUCCESS: Column pt_thanhtoan added to donhang table.")
    except Exception as e:
        print(f"INFO: Could not add column (it might already exist). Error: {e}")
