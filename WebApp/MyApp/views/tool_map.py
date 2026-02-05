# myapp/views/tool_map.py
from django.shortcuts import render
from myapp.models import CuaHang

def map_cua_hang(request):
    cua_hangs = CuaHang.objects.exclude(geom__isnull=True)
    return render(request, 'myapp/map_cuahang.html', {
        'cua_hangs': cua_hangs
    })