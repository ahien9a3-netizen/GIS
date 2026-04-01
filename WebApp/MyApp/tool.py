from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from .models import CuaHang, Kho

def store_geojson(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    stores = CuaHang.objects.all()
    features = []
    for store in stores:
        if store.geom:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": store.MaCH,
                    "name": store.Ten,
                    "address": store.DiaChi,
                    "phone": store.SDT or 'N/A',
                    "status": store.TrangThai,
                    "type": store.Loai,
                    "hinhanh": store.hinhanh
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [store.geom.x, store.geom.y] 
                }
            })
    return JsonResponse({"type": "FeatureCollection", "features": features})

def store_heatmap(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    stores = CuaHang.objects.filter(geom__isnull=False).values_list('geom', flat=True)
    warehouses = Kho.objects.filter(geom__isnull=False).values_list('geom', flat=True)
    
    data = [[p.y, p.x] for p in stores] + [[p.y, p.x] for p in warehouses]
    
    return JsonResponse(data, safe=False)

@require_GET
def service_area(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    try:
        center_lat = float(request.GET.get('lat'))
        center_lng = float(request.GET.get('lng'))
        radius_km = float(request.GET.get('radius', 2))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Tham số tọa độ hoặc bán kính không hợp lệ'}, status=400)
    
    center_point = Point(center_lng, center_lat, srid=4326)
    
    nearby_stores = CuaHang.objects.filter(
        geom__distance_lte=(center_point, D(km=radius_km))
    ).annotate(distance=Distance('geom', center_point)).order_by('distance')
    
    features = []
    for store in nearby_stores:
        if store.geom:
            dist_val = store.distance.km if hasattr(store.distance, 'km') else 0
            
            features.append({
                "type": "Feature",
                "properties": {
                    "id": store.MaCH, 
                    "name": store.Ten, 
                    "address": store.DiaChi,
                    "phone": store.SDT or 'N/A', 
                    "distance_km": round(dist_val, 2) 
                },
                "geometry": {"type": "Point", "coordinates": [store.geom.x, store.geom.y]}
            })
            
    return JsonResponse({
        'center': [center_lat, center_lng], 
        'radius_km': radius_km, 
        'count': len(features),
        'stores': {"type": "FeatureCollection", "features": features}
    })

def kho_geojson(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    kho_list = Kho.objects.all()
    features = []
    for wh in kho_list:
        if wh.geom:
            features.append({
                "type": "Feature",
                "properties": {"id": wh.MaKho, "name": wh.Ten, "address": wh.DiaChi, "type": wh.Loai, "hinhanh": wh.hinhanh},
                "geometry": {"type": "Point", "coordinates": [wh.geom.x, wh.geom.y]}
            })
    return JsonResponse({"type": "FeatureCollection", "features": features})

#def save(self, *args, **kwargs):
#       # Nếu chưa có khoảng cách, chúng ta sẽ bắt đầu tính toán
#       if not self.khoang_cach and self.cua_hang and self.kho:
#           # Chuyển tọa độ sang hệ phẳng (SRID 3857) để tính khoảng cách bằng mét
#           diem_cua_hang = self.cua_hang.geom.transform(3857, clone=True)
#           diem_kho = self.kho.geom.transform(3857, clone=True)
#           
#           # Tính khoảng cách
#           khoang_cach_met = diem_cua_hang.distance(diem_kho)
#           
#           # Đổi từ mét ra kilomet và làm tròn 1 chữ số thập phân
#           self.khoang_cach = round(khoang_cach_met / 1000, 1)
#
#       # Gọi lại hàm save() gốc của Django để lưu dữ liệu xuống database
#       super().save(*args, **kwargs)

def tinh_khoang_cach_va_thoi_gian(diem_cua_hang, diem_kho, van_toc_kmh=40):
    # 1. Chuyển hệ tọa độ sang mét phẳng (SRID 3857)
    diem_ch_met = diem_cua_hang.transform(3857, clone=True)
    diem_kho_met = diem_kho.transform(3857, clone=True)

    # 2. Tính khoảng cách (mét) rồi đổi ra km (làm tròn 1 chữ số thập phân)
    khoang_cach_met = diem_ch_met.distance(diem_kho_met)
    khoang_cach_km = round(khoang_cach_met / 1000, 1)

    # 3. Tính thời gian ra phút và ép kiểu về số nguyên (int)
    # Công thức: (km / (km/h)) * 60 = phút
    thoi_gian_phut = int((khoang_cach_km / van_toc_kmh) * 60)

    return khoang_cach_km, thoi_gian_phut