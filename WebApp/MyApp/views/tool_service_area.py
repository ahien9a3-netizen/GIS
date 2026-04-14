from django.shortcuts import render
from django.db import connection
from myapp.models import CuaHang

def service_area(request):
    buffer_geojson = None
    cua_hangs = CuaHang.objects.all()

    mach = request.GET.get('mach')

    if mach:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ST_AsGeoJSON(
                    ST_Buffer(geom::geography, 3000)::geometry
                )
                FROM cuahang
                WHERE mach = %s
            """, [mach])

            row = cursor.fetchone()
            if row:
                buffer_geojson = row[0]

    return render(request, 'myapp/service_area.html', {
        'cua_hangs': cua_hangs,
        'buffer_geojson': buffer_geojson,
        'selected_mach': mach
    })
