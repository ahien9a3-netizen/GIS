from django.contrib.gis.db import models

# ==================== SẢN PHẨM ====================
class SanPham(models.Model):
    MaSP = models.CharField(max_length=20, primary_key=True, db_column='masp')
    Ten = models.CharField(max_length=255, db_column='ten')
    Image = models.CharField(max_length=20, blank=True, null=True, db_column='image')
    DanhMuc = models.CharField(max_length=100, blank=True, null=True, db_column='danhmuc')
    MieuTa = models.TextField(blank=True, null=True, db_column='mieuta')
    TrangThai = models.CharField(max_length=50, blank=True, null=True, db_column='trangthai')

    class Meta:
        managed = False
        db_table = 'sanpham'
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Danh sách sản phẩm"

    def __str__(self):
        return f"{self.MaSP} - {self.Ten}"


# ==================== KHO ====================
class Kho(models.Model):
    MaKho = models.CharField(max_length=20, primary_key=True, db_column='makho')
    Ten = models.CharField(max_length=255, db_column='ten')
    Loai = models.CharField(max_length=50, blank=True, null=True, db_column='loai')
    DiaChi = models.TextField(blank=True, null=True, db_column='diachi')
    Icon = models.CharField(max_length=20, blank=True, null=True, db_column='icon')
    geom = models.PointField(srid=4326, db_column='geom')

    class Meta:
        managed = False
        db_table = 'kho'
        verbose_name = "Kho"
        verbose_name_plural = "Danh sách kho"

    def __str__(self):
        return f"{self.MaKho} - {self.Ten}"


# ==================== CỬA HÀNG ====================
class CuaHang(models.Model):
    MaCH = models.CharField(max_length=20, primary_key=True, db_column='mach')
    Ten = models.CharField(max_length=255, db_column='ten')
    Loai = models.CharField(max_length=50, blank=True, null=True, db_column='loai')
    Icon = models.CharField(max_length=20, blank=True, null=True, db_column='icon')
    DiaChi = models.TextField(blank=True, null=True, db_column='diachi')
    SDT = models.CharField(max_length=20, blank=True, null=True, db_column='sdt')
    TrangThai = models.CharField(max_length=50, blank=True, null=True, db_column='trangthai')
    geom = models.PointField(srid=4326, db_column='geom')

    class Meta:
        managed = False
        db_table = 'cuahang'
        verbose_name = "Cửa hàng"
        verbose_name_plural = "Danh sách cửa hàng"

    def __str__(self):
        return f"{self.MaCH} - {self.Ten}"


# ==================== NHÂN VIÊN ====================
class NhanVien(models.Model):
    MaNV = models.CharField(max_length=20, primary_key=True, db_column='manv')
    Ten = models.CharField(max_length=255, db_column='ten')
    SDT = models.CharField(max_length=20, blank=True, null=True, db_column='sdt')
    MatKhau = models.TextField(db_column='matkhau')
    Role = models.CharField(max_length=50, blank=True, null=True, db_column='role')

    class Meta:
        managed = False
        db_table = 'nhanvien'
        verbose_name = "Nhân viên"
        verbose_name_plural = "Danh sách nhân viên"

    def __str__(self):
        return f"{self.MaNV} - {self.Ten}"


# ==================== YÊU CẦU NHẬP KHO ====================
class YeuCauNhapKho(models.Model):
    MaYC = models.CharField(max_length=20, primary_key=True, db_column='mayc')
    Ngay = models.DateField(db_column='ngay')
    TrangThai = models.CharField(max_length=50, blank=True, null=True, db_column='trangthai')
    GhiChu = models.TextField(blank=True, null=True, db_column='ghichu')
    MaNV = models.ForeignKey(
        NhanVien,
        on_delete=models.CASCADE,
        db_column='manv',
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'yeucaunhapkho'
        verbose_name = "Yêu cầu nhập kho"
        verbose_name_plural = "Danh sách yêu cầu nhập kho"

    def __str__(self):
        return f"{self.MaYC} - {self.TrangThai}"


# ==================== HÀNG TỒN KHO ====================
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
    SoLuong = models.IntegerField(db_column='soluong')

    class Meta:
        managed = False
        db_table = 'hangtonkho'
        unique_together = (('MaKho', 'MaSP'),)
        verbose_name = "Hàng tồn kho"
        verbose_name_plural = "Danh sách hàng tồn kho"


# ==================== NHẬP KHO CHI TIẾT ====================
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
    SoLuong = models.IntegerField(db_column='soluong')

    class Meta:
        managed = False
        db_table = 'nhapkhochitiet'
        unique_together = (('MaYC', 'MaKho', 'MaSP'),)
        verbose_name = "Nhập kho chi tiết"
        verbose_name_plural = "Chi tiết nhập kho"


# ==================== KHÁCH HÀNG ====================
class KhachHang(models.Model):
    MaKH = models.CharField(max_length=20, primary_key=True)
    Ten = models.CharField(max_length=255)
    SDT = models.CharField(max_length=20, blank=True, null=True)
    Email = models.EmailField(blank=True, null=True)
    DiaChi = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách khách hàng"

    def __str__(self):
        return f"{self.MaKH} - {self.Ten}"


# ==================== ĐƠN HÀNG ====================
class DonHang(models.Model):
    STATUS_CHOICES = [
        ('cho_xu_ly', 'Chờ xử lý'),
        ('dang_giao', 'Đang giao'),
        ('da_hoan_thanh', 'Đã hoàn thành'),
        ('da_huy', 'Đã hủy'),
    ]
    MaDH = models.CharField(max_length=20, primary_key=True)
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    NgayTao = models.DateTimeField(auto_now_add=True)
    TongTien = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    TrangThai = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cho_xu_ly')

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Danh sách đơn hàng"

    def __str__(self):
        return self.MaDH


# ==================== GIAO HÀNG ====================
class GiaoHang(models.Model):
    MaGH = models.CharField(max_length=20, primary_key=True)
    DonHang = models.OneToOneField(DonHang, on_delete=models.CASCADE)
    NguoiGiao = models.CharField(max_length=255)
    SdtNguoiGiao = models.CharField(max_length=20)
    NgayGiao = models.DateTimeField(blank=True, null=True)
    TrangThai = models.CharField(max_length=50, default='Đang chuẩn bị')

    class Meta:
        verbose_name = "Giao hàng"
        verbose_name_plural = "Danh sách giao hàng"

    def __str__(self):
        return self.MaGH


# ==================== LEGACY: Store Model (compatibility) ====================
class Store(models.Model):
    """
    Legacy model - kept for backward compatibility
    """
    name = models.CharField(max_length=200, verbose_name="Tên cửa hàng")
    address = models.CharField(max_length=255, verbose_name="Địa chỉ")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    lat = models.FloatField(verbose_name="Vĩ độ", default=10.7769)
    lon = models.FloatField(verbose_name="Kinh độ", default=106.7009)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cửa hàng"
        verbose_name_plural = "Danh sách cửa hàng"
