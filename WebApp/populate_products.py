import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebApp.settings')
django.setup()

from MyApp.models import SanPham, DanhMuc

def populate_data():
    # 1. Create Categories
    categories = [
        ('DM_TL', 'Cửa hàng Tiện lợi'),
        ('DM_GD', 'Cửa hàng Gia dụng'),
        ('DM_DT', 'Cửa hàng Điện tử'),
    ]
    
    cat_objs = {}
    for code, name in categories:
        obj, created = DanhMuc.objects.get_or_create(MaDM=code, defaults={'Ten': name})
        cat_objs[code] = obj
        if created:
            print(f"Created category: {name}")

    # 2. Create Products
    products = [
        # Tiện Lợi
        ('TL01', 'Mì tôm Hảo Hảo', 'DM_TL', 'Mì gói quốc dân, hương vị tôm chua cay đặc trưng.', 'Đang bán'),
        ('TL02', 'Nước ngọt Coca-Cola 330ml', 'DM_TL', 'Nước giải khát có gas xua tan cơn khát.', 'Đang bán'),
        ('TL03', 'Sữa tươi Vinamilk 100%', 'DM_TL', 'Sữa tươi nguyên chất giàu canxi và vitamin.', 'Đang bán'),
        ('TL04', 'Bánh mì sandwich', 'DM_TL', 'Bánh mì tươi mới, phù hợp cho bữa sáng nhanh.', 'Đang bán'),
        
        # Gia Dụng
        ('GD01', 'Nồi cơm điện Sharp', 'DM_GD', 'Công nghệ nấu 3D giúp cơm chín đều và ngon hơn.', 'Đang bán'),
        ('GD02', 'Bộ lau nhà xoay 360', 'DM_GD', 'Tiện lợi, giúp việc dọn dẹp nhà cửa trở nên nhẹ nhàng.', 'Đang bán'),
        ('GD03', 'Chảo chống dính Sunhouse', 'DM_GD', 'Lớp chống dính cao cấp, an toàn cho sức khỏe.', 'Đang bán'),
        ('GD04', 'Bình đun siêu tốc 1.8L', 'DM_GD', 'Đun nước cực nhanh, tự động ngắt khi sôi.', 'Đang bán'),
        
        # Điện Tử
        ('DT01', 'Điện thoại iPhone 15', 'DM_DT', 'Siêu phẩm công nghệ với camera độ phân giải cao.', 'Đang bán'),
        ('DT02', 'Laptop ASUS Vivobook', 'DM_DT', 'Mạnh mẽ, sang trọng và cực kỳ mỏng nhẹ.', 'Đang bán'),
        ('DT03', 'Tai nghe Bluetooth Sony', 'DM_DT', 'Âm thanh chân thực, chống ồn hiệu quả.', 'Đang bán'),
        ('DT04', 'Loa Marshall Stanmore II', 'DM_DT', 'Thiết kế classic, chất âm đỉnh cao.', 'Đang bán'),
    ]

    for code, name, cat_code, desc, status in products:
        obj, created = SanPham.objects.update_or_create(
            MaSP=code,
            defaults={
                'Ten': name,
                'DanhMuc': cat_objs[cat_code],
                'MieuTa': desc,
                'TrangThai': status
            }
        )
        if created:
            print(f"Created product: {name}")
        else:
            print(f"Updated product: {name}")

if __name__ == '__main__':
    populate_data()
