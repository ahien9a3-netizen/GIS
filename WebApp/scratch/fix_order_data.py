import os
import sys
import django

# Add current directory to path
sys.path.append(os.getcwd())

# Setup Django environment - the project name is WebApp
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebApp.settings')
django.setup()

from MyApp.models import DonHang, YeuCauTraHang

def cleanup_order_statuses():
    # Tìm các đơn hàng đã hoàn tiền nhưng trạng thái gốc vẫn là 'Đã hoàn thành'
    orders = DonHang.objects.filter(
        TrangThai='Đã hoàn thành', 
        return_requests__TrangThai='Đã hoàn tiền'
    )
    
    count = 0
    for order in orders:
        order.TrangThai = 'Đã trả hàng'
        order.save()
        count += 1
        
    print(f'Successfully updated {count} orders to "Đã trả hàng".')

if __name__ == "__main__":
    cleanup_order_statuses()
