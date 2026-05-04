"""
Performance Optimization Utilities
Utilities for database query optimization and caching
"""

from django.views.decorators.cache import cache_page, cache_key_prefix
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.utils.decorators import method_decorator
from functools import wraps
import hashlib
import json


class QueryOptimizer:
    """Utilities for optimizing Django ORM queries"""
    
    @staticmethod
    def optimize_sanpham_queries(queryset):
        """Optimize SanPham queries with related data"""
        return queryset.select_related('DanhMuc').prefetch_related('danh_gias')
    
    @staticmethod
    def optimize_cuahang_queries(queryset):
        """Optimize CuaHang queries with related data"""
        return queryset.prefetch_related('danh_gias', 'nhan_su')
    
    @staticmethod
    def optimize_kho_queries(queryset):
        """Optimize Kho queries with related data"""
        return queryset.prefetch_related('hangtonkho_set__MaSP')
    
    @staticmethod
    def optimize_donhang_queries(queryset):
        """Optimize DonHang queries with related data"""
        return queryset.select_related('NguoiDung').prefetch_related('chi_tiet_items__SanPham')
    
    @staticmethod
    def optimize_hangtonkho_queries(queryset):
        """Optimize HangTonKho queries with related data"""
        return queryset.select_related('MaKho', 'MaSP')
    
    @staticmethod
    def optimize_yeucaunhapkho_queries(queryset):
        """Optimize YeuCauNhapKho queries with related data"""
        return queryset.select_related('MaNV').prefetch_related('nhapkhochitiet_set__MaSP', 'nhapkhochitiet_set__MaKho')


class CacheMixin:
    """Mixin to add caching to views"""
    
    cache_timeout = 300  # 5 minutes default
    cache_key = None
    
    def get_cache_key(self):
        """Generate cache key"""
        if self.cache_key:
            return self.cache_key
        
        return f"{self.__class__.__name__}:{self.request.user.id}"
    
    def get_cached_data(self, key):
        """Get data from cache"""
        return cache.get(key)
    
    def set_cached_data(self, key, value):
        """Set data in cache"""
        cache.set(key, value, self.cache_timeout)
    
    def clear_cache(self):
        """Clear cached data"""
        cache.delete(self.get_cache_key())


class CacheDecorator:
    """Decorator for caching function results"""
    
    def __init__(self, timeout=300):
        self.timeout = timeout
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = self._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, self.timeout)
            return result
        
        return wrapper
    
    @staticmethod
    def _generate_key(func_name, args, kwargs):
        """Generate cache key from function name and arguments"""
        # Convert arguments to string
        args_str = str(args)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
        combined = f"{func_name}:{args_str}:{kwargs_str}"
        
        # Create hash to keep key reasonable length
        return f"cache:{hashlib.md5(combined.encode()).hexdigest()}"


class QueryCounterMiddleware:
    """Middleware to count database queries (development only)"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection, reset_queries
        from django.conf import settings
        
        if settings.DEBUG:
            reset_queries()
        
        response = self.get_response(request)
        
        if settings.DEBUG:
            num_queries = len(connection.queries)
            if num_queries > 10:  # Log if more than 10 queries
                print(f"⚠️ {request.path} made {num_queries} database queries")
        
        return response


class PaginationOptimizer:
    """Optimize pagination queries"""
    
    @staticmethod
    def paginate_optimized(queryset, page, page_size=20):
        """Paginate queryset with optimization"""
        start = (page - 1) * page_size
        end = start + page_size
        
        # Get total count
        total_count = queryset.count()
        
        # Get paginated results
        results = list(queryset[start:end])
        
        return {
            'results': results,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }


class BulkOperationHelper:
    """Helper for bulk operations"""
    
    @staticmethod
    def bulk_update(model, objects, fields, batch_size=1000):
        """Bulk update objects"""
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i+batch_size]
            model.objects.bulk_update(batch, fields, batch_size=batch_size)
    
    @staticmethod
    def bulk_create(model, objects, batch_size=1000):
        """Bulk create objects"""
        created = []
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i+batch_size]
            result = model.objects.bulk_create(batch, batch_size=batch_size)
            created.extend(result)
        return created
    
    @staticmethod
    def bulk_delete(queryset, batch_size=1000):
        """Bulk delete objects efficiently"""
        ids = list(queryset.values_list('pk', flat=True)[:batch_size*100])
        
        deleted_count = 0
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            count, _ = queryset.model.objects.filter(pk__in=batch_ids).delete()
            deleted_count += count
        
        return deleted_count


def cache_page_optimized(timeout=300, cache_key_prefix=''):
    """Decorator to cache page with custom timeout"""
    def decorator(view):
        @cache_page(timeout)
        def wrapper(request, *args, **kwargs):
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


class DatabaseOptimizationTips:
    """
    Documentation class with optimization tips
    
    Usage tips:
    1. Always use select_related() for ForeignKey relationships
    2. Use prefetch_related() for ManyToMany and reverse ForeignKey relationships
    3. Use only() and defer() to load specific fields
    4. Use values() and values_list() when you don't need model instances
    5. Use count() without ordering for better performance
    6. Use exists() instead of count() to check if objects exist
    7. Use bulk_create() for creating multiple objects
    8. Use bulk_update() for updating multiple objects
    9. Avoid N+1 queries by using select_related() and prefetch_related()
    10. Use database-level pagination instead of Python-level slicing
    11. Add database indexes on frequently filtered fields
    12. Use cache for expensive queries
    13. Use raw SQL for complex queries
    14. Monitor query performance using Django Debug Toolbar
    """
    pass
