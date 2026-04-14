from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from django.core.validators import MinValueValidator, MaxValueValidator
# SẢN PHẨM
class SanPham(models.Model):
    TRANG_THAI_CHOICES = [
        ('Đang bán', 'Đang bán'),
        ('Ngừng bán', 'Ngừng bán'),
    ]

    MaSP = models.CharField(max_length=20, primary_key=True, db_column='masp')
    Ten = models.CharField(max_length=255, db_column='ten')
    Image = models.ImageField(upload_to='products/',max_length=255, blank=True, null=True, db_column='image')
    DanhMuc = models.ForeignKey('DanhMuc', on_delete=models.SET_NULL, blank=True, null=True, db_column='danhmuc')
    MieuTa = models.TextField(blank=True, null=True, db_column='mieuta')
    TrangThai = models.CharField(max_length=50, choices=TRANG_THAI_CHOICES, db_column='trangthai')
    Gia = models.DecimalField(max_digits=12, decimal_places=0, default=0, db_column='gia', verbose_name="Giá bán")

    class Meta:
        managed = True
        db_table = 'sanpham'
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Danh sách sản phẩm"

    def __str__(self):
        return f"{self.MaSP} - {self.Ten}"

# ĐÁNH GIÁ SẢN PHẨM
class DanhGia(models.Model):
    SanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE, related_name='danh_gias', db_column='masp')
    NguoiDung = models.CharField(max_length=255, db_column='nguoidung')
    Diem = models.IntegerField(db_column='diem')
    BinhLuan = models.TextField(db_column='binhluan')
    NgayTao = models.DateTimeField(auto_now_add=True, db_column='ngaytao')

    class Meta:
        managed = True
        db_table = 'danhgia'
        verbose_name = "Đánh giá"
        verbose_name_plural = "Danh sách đánh giá"

# ĐÁNH GIÁ CỬA HÀNG
class DanhGiaCuaHang(models.Model):
    CuaHang = models.ForeignKey('CuaHang', on_delete=models.CASCADE, related_name='danh_gias', db_column='mach')
    NguoiDung = models.CharField(max_length=255, db_column='nguoidung')
    Diem = models.IntegerField(db_column='diem')
    BinhLuan = models.TextField(db_column='binhluan')
    NgayTao = models.DateTimeField(auto_now_add=True, db_column='ngaytao')

    class Meta:
        managed = True
        db_table = 'danhgiacuahang'
        verbose_name = "Đánh giá cửa hàng"
        verbose_name_plural = "Danh sách đánh giá cửa hàng"
#  KHO 
class Kho(models.Model):
    KHO_LOAI_CHOICES = [
        ('Kho Tổng', 'Kho Tổng'),
        ('Kho Chi Nhánh', 'Kho Chi Nhánh'),
    ]

    MaKho = models.CharField(max_length=20, primary_key=True, db_column='makho')
    Ten = models.CharField(max_length=255, db_column='ten')
    Loai = models.CharField(max_length=50, choices=KHO_LOAI_CHOICES, db_column='loai')
    DiaChi = models.TextField(blank=True, null=True, db_column='diachi')
    Icon = models.CharField(max_length=20, blank=True, null=True, db_column='icon')
    hinhanh = ArrayField(models.CharField(max_length=255), blank=True, null=True, db_column='hinhanh')
    geom = models.PointField(srid=4326, db_column='geom')
    MoTa = RichTextField(blank=True, null=True, db_column='mota', verbose_name="Mô tả")

    class Meta:
        managed = True
        db_table = 'kho'
        verbose_name = "Kho"
        verbose_name_plural = "Danh sách kho"

    def __str__(self):
        return f"{self.MaKho} - {self.Ten}"

    def clean(self):
        # Kiểm tra khoảng cách tối thiểu 2 mét (xấp xỉ 0.00002 độ)
        min_dist = 0.00002
        
        # Kiểm tra với các kho khác
        other_wh = Kho.objects.exclude(MaKho=self.MaKho).filter(geom__dwithin=(self.geom, min_dist))
        if other_wh.exists():
            raise ValidationError(f"Tọa độ này quá gần với kho '{other_wh.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")
            
        # Kiểm tra với các cửa hàng
        nearby_stores = CuaHang.objects.filter(geom__dwithin=(self.geom, min_dist))
        if nearby_stores.exists():
            raise ValidationError(f"Tọa độ này quá gần với cửa hàng '{nearby_stores.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")


#  CỬA HÀNG 
class CuaHang(models.Model):
    LOAI_CHOICES = [
        ('Tiện Lợi', 'Tiện Lợi'),
        ('Gia Dụng', 'Gia Dụng'),
        ('Điện Tử', 'Điện Tử'),
    ]

    TRANG_THAI_CHOICES = [
        ('Hoạt động', 'Hoạt động'),
        ('Tạm ngưng', 'Tạm ngưng'),
        ('Vô hiệu hóa', 'Vô hiệu hóa'),
    ]
    
    MaCH = models.CharField(max_length=20, primary_key=True, db_column='mach')
    Ten = models.CharField(max_length=255, db_column='ten')
    Loai = models.CharField(max_length=50, choices=LOAI_CHOICES, db_column='loai')
    Icon = models.CharField(max_length=20, blank=True, null=True, db_column='icon')
    DiaChi = models.TextField(blank=True, null=True, db_column='diachi')
    SDT = models.CharField(max_length=20, blank=True, null=True, db_column='sdt')
    hinhanh = ArrayField(models.CharField(max_length=255), blank=True, null=True, db_column='hinhanh')
    TrangThai = models.CharField(max_length=50, choices=TRANG_THAI_CHOICES, db_column='trangthai')
    geom = models.PointField(srid=4326, db_column='geom')
    GioMoCua = models.TimeField(null=True, blank=True, db_column='giomocua', verbose_name="Giờ mở cửa")
    GioDongCua = models.TimeField(null=True, blank=True, db_column='giodongcua', verbose_name="Giờ đóng cửa")
    MoTa = RichTextField(blank=True, null=True, db_column='mota', verbose_name="Mô tả")

    class Meta:
        managed = True
        db_table = 'cuahang'
        verbose_name = "Cửa hàng"
        verbose_name_plural = "Danh sách cửa hàng"

    def __str__(self):
        return f"{self.MaCH} - {self.Ten}"

    def clean(self):
        # Kiểm tra khoảng cách tối thiểu 2 mét (xấp xỉ 0.00002 độ)
        min_dist = 0.00002
        
        # Kiểm tra với các cửa hàng khác
        other_st = CuaHang.objects.exclude(MaCH=self.MaCH).filter(geom__dwithin=(self.geom, min_dist))
        if other_st.exists():
            raise ValidationError(f"Tọa độ này quá gần với cửa hàng '{other_st.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")
            
        # Kiểm tra với các kho hàng
        nearby_wh = Kho.objects.filter(geom__dwithin=(self.geom, min_dist))
        if nearby_wh.exists():
            raise ValidationError(f"Tọa độ này quá gần với kho '{nearby_wh.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")


#  NHÂN VIÊN 
class NhanVien(models.Model):
    
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Nhân Viên', 'Nhân Viên'),
        ('Kế Toán', 'Kế Toán'),
        ('User', 'User'),
    ]
    
    
    MaNV = models.CharField(max_length=20, primary_key=True, db_column='manv')
    Ten = models.CharField(max_length=255, db_column='ten')
    SDT = models.CharField(max_length=20, blank=True, null=True, db_column='sdt')
    Email = models.EmailField(max_length=255, blank=True, null=True, db_column='email')
    MatKhau = models.TextField(db_column='matkhau')
    Role = models.CharField(max_length=50, choices=ROLE_CHOICES, db_column='role')

    class Meta:
        managed = True
        db_table = 'nhanvien'
        verbose_name = "Nhân viên"
        verbose_name_plural = "Danh sách nhân viên"

    def __str__(self):
        return f"{self.MaNV} - {self.Ten}"

#  YÊU CẦU NHẬP KHO 
class YeuCauNhapKho(models.Model):
    TRANG_THAI_CHOICES = [
        ('Chờ duyệt', 'Chờ duyệt'),
        ('Đã duyệt', 'Đã duyệt'),
    ]

    MaYC = models.CharField(max_length=20, primary_key=True, db_column='mayc')
    Ngay = models.DateField(db_column='ngay')
    TrangThai = models.CharField(max_length=50, choices=TRANG_THAI_CHOICES, db_column='trangthai')
    GhiChu = models.TextField(blank=True, null=True, db_column='ghichu')
    MaNV = models.ForeignKey(
        NhanVien,
        on_delete=models.CASCADE,
        db_column='manv',
        blank=True,
        null=True
    )

    class Meta:
        managed = True
        db_table = 'yeucaunhapkho'
        verbose_name = "Yêu cầu nhập kho"
        verbose_name_plural = "Danh sách yêu cầu nhập kho"

    def __str__(self):
        return f"{self.MaYC} - {self.TrangThai}"


#  HÀNG TỒN KHO 
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
        managed = True
        db_table = 'hangtonkho'
        unique_together = (('MaKho', 'MaSP'),)
        verbose_name = "Hàng tồn kho"
        verbose_name_plural = "Danh sách hàng tồn kho"


#  NHẬP KHO CHI TIẾT 
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
        managed = True
        db_table = 'nhapkhochitiet'
        unique_together = (('MaYC', 'MaKho', 'MaSP'),)
        verbose_name = "Nhập kho chi tiết"
        verbose_name_plural = "Chi tiết nhập kho"


#  YÊU CẦU XUẤT KHO 
class YeuCauXuatKho(models.Model):
    TRANG_THAI_CHOICES = [
        ('Mới', 'Mới'),
        ('Đã xuất', 'Đã xuất'),
        ('Đã hủy', 'Đã hủy'),
    ]

    LY_DO_CHOICES = [
        ('Bán hàng', 'Bán hàng'),
        ('Trả hàng nhà cung cấp', 'Trả hàng nhà cung cấp'),
        ('Hàng hỏng', 'Hàng hỏng'),
        ('Chuyển kho', 'Chuyển kho'),
        ('Khác', 'Khác'),
    ]

    MaPX = models.CharField(max_length=20, primary_key=True, db_column='mapx', verbose_name="Mã phiếu xuất")
    Ngay = models.DateField(auto_now_add=True, db_column='ngay', verbose_name="Ngày xuất")
    LyDo = models.CharField(max_length=50, choices=LY_DO_CHOICES, default='Bán hàng', db_column='lydo', verbose_name="Lý do xuất")
    DonHang = models.ForeignKey('DonHang', on_delete=models.SET_NULL, null=True, blank=True, db_column='madh', verbose_name="Đơn hàng liên kết")
    TrangThai = models.CharField(max_length=50, choices=TRANG_THAI_CHOICES, default='Mới', db_column='trangthai', verbose_name="Trạng thái")
    GhiChu = models.TextField(blank=True, null=True, db_column='ghichu', verbose_name="Ghi chú")
    MaNV = models.ForeignKey('NhanVien', on_delete=models.CASCADE, db_column='manv', verbose_name="Nhân viên thực hiện")

    class Meta:
        managed = True
        db_table = 'yeucauxuatkho'
        verbose_name = "Yêu cầu xuất kho"
        verbose_name_plural = "Danh sách yêu cầu xuất kho"

    def __str__(self):
        return f"{self.MaPX} - {self.TrangThai}"

#  XUẤT KHO CHI TIẾT 
class XuatKhoChiTiet(models.Model):
    PhieuXuat = models.ForeignKey(YeuCauXuatKho, on_delete=models.CASCADE, related_name='items', db_column='mapx')
    MaKho = models.ForeignKey('Kho', on_delete=models.CASCADE, db_column='makho')
    MaSP = models.ForeignKey('SanPham', on_delete=models.CASCADE, db_column='masp')
    SoLuong = models.PositiveIntegerField(db_column='soluong')

    class Meta:
        managed = True
        db_table = 'xuatkhochitiet'
        unique_together = (('PhieuXuat', 'MaKho', 'MaSP'),)
        verbose_name = "Xuất kho chi tiết"
        verbose_name_plural = "Chi tiết xuất kho"


#  DANH MỤC 
class DanhMuc(models.Model):
    MaDM = models.CharField(max_length=20, primary_key=True, db_column='madm')
    Ten = models.CharField(max_length=255, db_column='tendm')

    class Meta:
        managed = True
        db_table = 'danhmuc'
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh sách danh mục"

    def __str__(self):
        return f"{self.MaDM} - {self.Ten}"

#  PHÂN BỔ CUNG CẤP
class PhanBoCungCap(models.Model):
    cua_hang = models.ForeignKey('CuaHang', on_delete=models.CASCADE)
    kho = models.ForeignKey('Kho', on_delete=models.CASCADE)
    khoang_cach = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True) 
    thoi_gian = models.IntegerField(null=True, blank=True)
    uu_tien = models.IntegerField()

    class Meta:
        unique_together = (('cua_hang', 'kho'),)
    def save(self, *args, **kwargs):
        from .tool import tinh_khoang_cach_va_thoi_gian 
        if not self.khoang_cach and self.cua_hang and self.kho:
            km, phut = tinh_khoang_cach_va_thoi_gian(self.cua_hang.geom, self.kho.geom)
            self.khoang_cach = km
            self.thoi_gian = phut

        super().save(*args, **kwargs)

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

# GIỎ HÀNG
class GioHang(models.Model):
    NguoiDung = models.OneToOneField(NhanVien, on_delete=models.CASCADE, related_name='gio_hang', db_column='manv', null=True, blank=True)
    SessionID = models.CharField(max_length=255, null=True, blank=True, db_column='session_id') # Cho khách vãng lai
    NgayTao = models.DateTimeField(auto_now_add=True, db_column='ngaytao')
    NgayCapNhat = models.DateTimeField(auto_now=True, db_column='ngaycapnhat')

    class Meta:
        managed = True
        db_table = 'giohang'
        verbose_name = "Giỏ hàng"
        verbose_name_plural = "Danh sách giỏ hàng"

class ChiTietGioHang(models.Model):
    GioHang = models.ForeignKey(GioHang, on_delete=models.CASCADE, related_name='items', db_column='magh')
    SanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE, db_column='masp')
    SoLuong = models.PositiveIntegerField(default=1, db_column='soluong')

    class Meta:
        managed = True
        db_table = 'chitietgiohang'
        verbose_name = "Chi tiết giỏ hàng"
        verbose_name_plural = "Chi tiết các giỏ hàng"
        unique_together = (('GioHang', 'SanPham'),)

# ĐƠN HÀNG
class DonHang(models.Model):
    TRANG_THAI_DH = [
        ('Đang xử lý', 'Đang xử lý'),
        ('Đang giao', 'Đang giao'),
        ('Đã hoàn thành', 'Đã hoàn thành'),
        ('Đã hủy', 'Đã hủy'),
        ('Đã trả hàng', 'Đã trả hàng'),
    ]

    PHUONG_THUC_TT = [
        ('COD', 'Thanh toán khi nhận hàng'),
        ('MoMo', 'Ví điện tử MoMo'),
        ('Bank', 'Chuyển khoản Ngân hàng'),
    ]

    MaDH = models.CharField(max_length=20, primary_key=True, db_column='madh')
    NguoiDung = models.ForeignKey(NhanVien, on_delete=models.SET_NULL, null=True, blank=True, db_column='manv')
    
    # Thông tin nhận hàng (để linh hoạt nếu người nhận khác người đặt)
    TenNguoiNhan = models.CharField(max_length=255, db_column='tennguoinhan')
    SDT_Nhan = models.CharField(max_length=20, db_column='sdt_nhan')
    DiaChi_Nhan = models.TextField(db_column='diachi_nhan')
    
    TongTien = models.DecimalField(max_digits=15, decimal_places=0, db_column='tongtien')
    PhuongThucThanhToan = models.CharField(max_length=50, choices=PHUONG_THUC_TT, default='COD', db_column='pt_thanhtoan')
    TrangThai = models.CharField(max_length=50, choices=TRANG_THAI_DH, default='Đang xử lý', db_column='trangthai')
    GhiChu = models.TextField(blank=True, null=True, db_column='ghichu')

# BẢNG ĐÁNH GIÁ CỬA HÀNG
class DanhGiaCuaHang(models.Model):
    CuaHang = models.ForeignKey(CuaHang, on_delete=models.CASCADE, related_name='danh_gia', db_column='mach')
    NhanVien = models.ForeignKey(NhanVien, on_delete=models.CASCADE, db_column='manv')
    SoSao = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], db_column='sosao', verbose_name="Số sao")
    NhanXet = models.TextField(blank=True, null=True, db_column='nhanxet', verbose_name="Nhận xét")
    NgayTao = models.DateTimeField(auto_now_add=True, db_column='ngaytao')

    class Meta:
        managed = True
        db_table = 'donhang'
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Danh sách đơn hàng"

    def __str__(self):
        return f"{self.MaDH} - {self.TenNguoiNhan}"

class ChiTietDonHang(models.Model):
    DonHang = models.ForeignKey(DonHang, on_delete=models.CASCADE, related_name='items', db_column='madh')
    SanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE, db_column='masp')
    SoLuong = models.PositiveIntegerField(db_column='soluong')
    GiaBan = models.DecimalField(max_digits=12, decimal_places=0, db_column='giaban') # Lưu giá tại thời điểm mua

    class Meta:
        managed = True
        db_table = 'chitietdonhang'
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Chi tiết các đơn hàng"

class YeuCauTraHang(models.Model):
    TRANG_THAI_CHOICES = [
        ('Mới', 'Mới'),
        ('Đang xử lý', 'Đang xử lý'),
        ('Đã hoàn tiền', 'Đã hoàn tiền'),
        ('Từ chối', 'Từ chối'),
    ]
    
    MaYCTH = models.CharField(max_length=20, primary_key=True, verbose_name="Mã yêu cầu")
    DonHang = models.ForeignKey(DonHang, on_delete=models.CASCADE, related_name='return_requests', verbose_name="Đơn hàng")
    SdtLienHe = models.CharField(max_length=20, null=True, blank=True, verbose_name="Số điện thoại liên hệ")
    EmailLienHe = models.EmailField(null=True, blank=True, verbose_name="Email liên hệ")
    SoTaiKhoanNH = models.CharField(max_length=100, null=True, blank=True, verbose_name="Số tài khoản ngân hàng")
    SoTaiKhoanMoMo = models.CharField(max_length=100, null=True, blank=True, verbose_name="Số tài khoản MoMo")
    LyDo = models.TextField(verbose_name="Lý do trả hàng")
    AnhHoaDon = models.ImageField(upload_to='returns/invoices/', null=True, blank=True, verbose_name="Ảnh hóa đơn")
    AnhMinhChung = models.ImageField(upload_to='returns/proof/', null=True, blank=True, verbose_name="Ảnh minh chứng")
    GhiChuAdmin = models.TextField(null=True, blank=True, verbose_name="Ghi chú của Admin")
    SoTienHoan = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Số tiền hoàn lại")
    TrangThai = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default='Mới', verbose_name="Trạng thái")
    NgayTao = models.DateTimeField(auto_now_add=True, verbose_name="Ngày yêu cầu")
    NgayXuLy = models.DateTimeField(null=True, blank=True, verbose_name="Ngày xử lý")

    class Meta:
        managed = True
        db_table = 'yeucautrahang'
        verbose_name = "Yêu cầu trả hàng"
        verbose_name_plural = "Các yêu cầu trả hàng"
        ordering = ['-NgayTao']

    def __str__(self):
        return f"YCTH {self.MaYCTH} - Đơn {self.DonHang.MaDH}"
        db_table = 'danhgiacuahang'
        ordering = ['-NgayTao'] # Sắp xếp đánh giá mới nhất lên đầu
