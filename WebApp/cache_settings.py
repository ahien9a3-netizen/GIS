# Django Cache Configuration for WebApp
# Add this to your settings.py to enable caching

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'webapp-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        }
    }
}

# For production, use Redis cache:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'redis.Redis',
#         },
#         'KEY_PREFIX': 'webapp',
#         'TIMEOUT': 300,  # 5 minutes default
#     }
# }

# Cache timeout configurations
CACHE_TIMEOUT_SANPHAM = 600  # 10 minutes for product list
CACHE_TIMEOUT_CUAHANG = 600  # 10 minutes for store list
CACHE_TIMEOUT_KHO = 600      # 10 minutes for warehouse list
CACHE_TIMEOUT_HANGTONKHO = 300  # 5 minutes for inventory (changes frequently)
CACHE_TIMEOUT_DONHANG = 300  # 5 minutes for orders (changes frequently)

# Session cache configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Database query logging (development only)
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }
