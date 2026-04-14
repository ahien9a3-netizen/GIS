from django.shortcuts import render
from django.db import connection
from myapp.models import CuaHang

def density_cua_hang(request):
    count = None
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if lat and lon:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM cuahang
                WHERE ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    1000
                )
            """, [lon, lat])
            count = cursor.fetchone()[0]

    return render(request, 'myapp/density.html', {
        'count': count,
        'lat': lat,
        'lon': lon
    })
