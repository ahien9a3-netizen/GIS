import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebApp.settings')
django.setup()

from MyApp.models import CuaHang, Kho, SanPham, HangTonKho, PhanBoCungCap

def populate_inventory():
    stores = CuaHang.objects.all()
    warehouses = Kho.objects.all()
    products = SanPham.objects.all()

    if not stores or not warehouses or not products:
        print("Missing stores, warehouses or products. Please run initial data setup first.")
        return

    # 1. Link each store to 1-2 random warehouses (PhanBoCungCap)
    print("Linking stores to warehouses...")
    for store in stores:
        # Check if already linked
        if not PhanBoCungCap.objects.filter(cua_hang=store).exists():
            target_warehouses = random.sample(list(warehouses), min(2, len(warehouses)))
            for i, wh in enumerate(target_warehouses):
                PhanBoCungCap.objects.create(
                    cua_hang=store,
                    kho=wh,
                    uu_tien=i+1
                )
    
    # 2. Add random products to each warehouse (HangTonKho)
    print("Adding products to warehouses...")
    for wh in warehouses:
        # Pick 10-15 random products
        target_products = random.sample(list(products), min(15, len(products)))
        for p in target_products:
            # Update or create
            HangTonKho.objects.update_or_create(
                MaKho=wh,
                MaSP=p,
                defaults={'SoLuong': random.randint(10, 100)}
            )

    print("Successfully populated store inventory association.")

if __name__ == "__main__":
    populate_inventory()
