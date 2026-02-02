from django.db import models

class SanPham(models.Model):
    ten = models.CharField(max_length=255)
    danh_muc = models.CharField(max_length=100)
    trang_thai = models.BooleanField(default=True)

    def __str__(self):
        return self.ten
