from django.shortcuts import render
from .models import CuaHang, Kho, SanPham, HangTonKho

def dashboard(request):
    context = {
        'tong_cua_hang': CuaHang.objects.count(),
        'tong_kho': Kho.objects.count(),
        'tong_san_pham': SanPham.objects.count(),
        'tong_ton_kho': HangTonKho.objects.aggregate(
            total=models.Sum('SoLuong')
        )['total'] or 0,
    }
    return render(request, 'myapp/dashboard.html', context)
from django.core.serializers import serialize

def cuahang(request):
    data = serialize(
        'geojson',
        CuaHang.objects.exclude(geom__isnull=True),
        geometry_field='geom',
        fields=('Ten', 'DiaChi')
    )
    return render(request, 'myapp/cuahang.html', {
        'geojson': data
    })

def kho(request):
    data = Kho.objects.all()
    return render(request, 'myapp/kho.html', {'data': data})
