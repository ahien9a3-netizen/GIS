import os
import sys
import django

# Add current directory to path
sys.path.append(os.getcwd())

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebApp.settings')
django.setup()

from MyApp.models import DonHang

def update_order_status_logic():
    # Chuyển tất cả đơn hàng từ 'Mới' sang 'Đang xử lý'
    orders = DonHang.objects.filter(TrangThai='Mới')
    count = orders.update(TrangThai='Đang xử lý')
    print(f'Done! Updated {count} orders from "Mới" to "Đang xử lý".')

if __name__ == "__main__":
    update_order_status_logic()
