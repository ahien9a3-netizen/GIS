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
                    "type": store.Loai
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
    
    layer_type = request.GET.get('type', 'all')
    data = []

    if layer_type in ['all', 'TienLoi', 'GiaDung', 'DienTu']:
        stores_query = CuaHang.objects.filter(geom__isnull=False)
        if layer_type == 'TienLoi':
            stores_query = stores_query.filter(Loai='Tiện Lợi')
        elif layer_type == 'GiaDung':
            stores_query = stores_query.filter(Loai='Gia Dụng')
        elif layer_type == 'DienTu':
            stores_query = stores_query.filter(Loai='Điện Tử')
        
        stores = stores_query.values_list('geom', flat=True)
        data.extend([[p.y, p.x] for p in stores])

    if layer_type in ['all', 'KhoHang']:
        warehouses = Kho.objects.filter(geom__isnull=False).values_list('geom', flat=True)
        data.extend([[p.y, p.x] for p in warehouses])
    
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
                    "type": store.Loai,
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
                "properties": {"id": wh.MaKho, "name": wh.Ten, "address": wh.DiaChi, "type": wh.Loai},
                "geometry": {"type": "Point", "coordinates": [wh.geom.x, wh.geom.y]}
            })
    return JsonResponse({"type": "FeatureCollection", "features": features})
