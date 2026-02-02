from django.shortcuts import render

from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello GIS WebApp 🚀")

def home(request):
    return render(request, 'home.html')

def product_list(request):
    products = [
        {'ten': 'Tivi Samsung', 'so_luong': 10},
        {'ten': 'Tủ lạnh LG', 'so_luong': 5},
    ]
    return render(request, 'products/list.html', {'products': products})

def warehouse_list(request):
    warehouses = [
        {'ten': 'Kho Hà Nội', 'dia_chi': 'HN'},
        {'ten': 'Kho TP.HCM', 'dia_chi': 'HCM'},
    ]
    return render(request, 'warehouse/list.html', {'warehouses': warehouses})

