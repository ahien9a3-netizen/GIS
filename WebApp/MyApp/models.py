from django.db import models

class SanPham(models.Model):
    MaSP = models.CharField(max_length=20, primary_key=True)
    Ten = models.CharField(max_length=255)
    Image = models.CharField(max_length=20, null=True, blank=True)
    DanhMuc = models.CharField(max_length=100, null=True, blank=True)
    MieuTa = models.TextField(null=True, blank=True)
    TrangThai = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'sanpham'
class Kho(models.Model):
    MaKho = models.CharField(max_length=20, primary_key=True)
    Ten = models.CharField(max_length=255)
    Loai = models.CharField(max_length=50, null=True, blank=True)
    DiaChi = models.TextField(null=True, blank=True)
    Icon = models.CharField(max_length=20, null=True, blank=True)
    geom = models.TextField()

    class Meta:
        managed = False
        db_table = 'kho'
class CuaHang(models.Model):
    MaCH = models.CharField(max_length=20, primary_key=True)
    Ten = models.CharField(max_length=255)
    Loai = models.CharField(max_length=50, null=True, blank=True)
    Icon = models.CharField(max_length=20, null=True, blank=True)
    DiaChi = models.TextField(null=True, blank=True)
    SDT = models.CharField(max_length=20, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, null=True, blank=True)
    geom = models.TextField()

    class Meta:
        managed = False
        db_table = 'cuahang'
class NhanVien(models.Model):
    MaNV = models.CharField(max_length=20, primary_key=True)
    Ten = models.CharField(max_length=255)
    SDT = models.CharField(max_length=20, null=True, blank=True)
    MatKhau = models.TextField()
    Role = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'nhanvien'
class YeuCauNhapKho(models.Model):
    MaYC = models.CharField(max_length=20, primary_key=True)
    Ngay = models.DateField()
    TrangThai = models.CharField(max_length=50, null=True, blank=True)
    GhiChu = models.TextField(null=True, blank=True)
    MaNV = models.ForeignKey(
        NhanVien,
        on_delete=models.CASCADE,
        db_column='manv'
    )

    class Meta:
        managed = False
        db_table = 'yeucaunhapkho'
class HangTonKho(models.Model):
    MaKho = models.ForeignKey(
        Kho,
        on_delete=models.CASCADE,
        db_column='makho'
    )
    MaSP = models.ForeignKey(
        SanPham,
        on_delete=models.CASCADE,
        db_column='masp'
    )
    SoLuong = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'hangtonkho'
        unique_together = (('MaKho', 'MaSP'),)
class NhapKhoChiTiet(models.Model):
    MaYC = models.ForeignKey(
        YeuCauNhapKho,
        on_delete=models.CASCADE,
        db_column='mayc'
    )
    MaKho = models.ForeignKey(
        Kho,
        on_delete=models.CASCADE,
        db_column='makho'
    )
    MaSP = models.ForeignKey(
        SanPham,
        on_delete=models.CASCADE,
        db_column='masp'
    )
    SoLuong = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'nhapkhochitiet'
        unique_together = (('MaYC', 'MaKho', 'MaSP'),)
