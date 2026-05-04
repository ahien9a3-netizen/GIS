from django import forms
import re
from .models import YeuCauNhapKho, YeuCauXuatKho, CuaHang, Kho, NhanVien, SanPham, DanhMuc, HangTonKho


# ============================================================
#  CỬA HÀNG
# ============================================================
class CuaHangForm(forms.ModelForm):
    class Meta:
        model = CuaHang
        fields = ['MaCH', 'Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai', 'geom', 'MoTa']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['MaCH'].disabled = True

    def clean_MaCH(self):
        ma_ch = self.cleaned_data.get('MaCH')
        if self.instance.pk:
            return self.instance.MaCH
        if CuaHang.objects.filter(MaCH=ma_ch).exists():
            raise forms.ValidationError("Mã cửa hàng này đã tồn tại trong hệ thống.")
        return ma_ch

    def clean_SDT(self):
        sdt = self.cleaned_data.get('SDT', '')
        if sdt:
            sdt = sdt.strip()
            if not re.match(r'^0\d{9,10}$', sdt):
                raise forms.ValidationError("Số điện thoại không hợp lệ (phải bắt đầu bằng 0, 10-11 chữ số).")
            qs = CuaHang.objects.filter(SDT=sdt)
            if self.instance.pk:
                qs = qs.exclude(MaCH=self.instance.MaCH)
            if qs.exists():
                raise forms.ValidationError("Số điện thoại này đã được đăng ký cho cửa hàng khác.")
        return sdt

    def clean(self):
        cleaned_data = super().clean()
        geom = cleaned_data.get('geom')
        if geom:
            min_dist = 0.0001
            other_st = CuaHang.objects.exclude(MaCH=self.instance.MaCH).filter(geom__dwithin=(geom, min_dist))
            if other_st.exists():
                raise forms.ValidationError(
                    f"Tọa độ này quá gần với cửa hàng '{other_st.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")
            nearby_wh = Kho.objects.filter(geom__dwithin=(geom, min_dist))
            if nearby_wh.exists():
                raise forms.ValidationError(
                    f"Tọa độ này quá gần với kho '{nearby_wh.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")
        return cleaned_data


# ============================================================
#  KHO HÀNG
# ============================================================
class KhoForm(forms.ModelForm):
    class Meta:
        model = Kho
        fields = ['MaKho', 'Ten', 'Loai', 'DiaChi', 'geom', 'MoTa']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['MaKho'].disabled = True

    def clean(self):
        print("=== KhoForm.clean() called! ===")
        cleaned_data = super().clean()
        geom = cleaned_data.get('geom')
        print(f"=== geom: {geom} ===")
        if geom:
            min_dist = 0.0001
            other_wh = Kho.objects.exclude(MaKho=self.instance.MaKho).filter(geom__dwithin=(geom, min_dist))
            print(f"=== other_wh.count(): {other_wh.count()} ===")
            if other_wh.exists():
                print("=== RAISING ERROR for other warehouse! ===")
                raise forms.ValidationError(
                    f"Tọa độ này quá gần với kho '{other_wh.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")
            nearby_stores = CuaHang.objects.filter(geom__dwithin=(geom, min_dist))
            print(f"=== nearby_stores.count(): {nearby_stores.count()} ===")
            if nearby_stores.exists():
                print("=== RAISING ERROR for store! ===")
                raise forms.ValidationError(
                    f"Tọa độ này quá gần với cửa hàng '{nearby_stores.first().Ten}'. Vui lòng chọn vị trí khác (cách ít nhất 2m).")
        return cleaned_data


# ============================================================
#  NHÂN VIÊN  ← ĐÃ TĂNG CƯỜNG VALIDATION
# ============================================================
class NhanVienForm(forms.ModelForm):
    class Meta:
        model = NhanVien
        fields = ['MaNV', 'Ten', 'SDT', 'Email', 'Role', 'MatKhau']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['MaNV'].disabled = True

    def clean_MaNV(self):
        ma_nv = self.cleaned_data.get('MaNV')
        if not self.instance.pk:
            if NhanVien.objects.filter(MaNV=ma_nv).exists():
                raise forms.ValidationError("Mã nhân viên này đã tồn tại trong hệ thống.")
        return ma_nv

    def clean_Ten(self):
        ten = self.cleaned_data.get('Ten', '').strip()
        if not ten:
            raise forms.ValidationError("Tên nhân viên không được để trống.")
        return ten

    def clean_SDT(self):
        sdt = self.cleaned_data.get('SDT', '')
        if sdt:
            sdt = sdt.strip()
            if not re.match(r'^0\d{9,10}$', sdt):
                raise forms.ValidationError("Số điện thoại không hợp lệ (phải bắt đầu bằng 0, 10–11 chữ số).")
            qs = NhanVien.objects.filter(SDT=sdt)
            if self.instance.pk:
                qs = qs.exclude(MaNV=self.instance.MaNV)
            if qs.exists():
                raise forms.ValidationError("Số điện thoại này đã được đăng ký cho nhân viên khác.")
        return sdt

    def clean_Email(self):
        email = self.cleaned_data.get('Email', '')
        if email:
            email = email.strip()
            qs = NhanVien.objects.filter(Email__iexact=email)
            if self.instance.pk:
                qs = qs.exclude(MaNV=self.instance.MaNV)
            if qs.exists():
                raise forms.ValidationError("Email này đã được sử dụng bởi nhân viên khác.")
        return email

    def clean_MatKhau(self):
        mat_khau = self.cleaned_data.get('MatKhau', '')
        if len(mat_khau) < 6:
            raise forms.ValidationError("Mật khẩu phải có ít nhất 6 ký tự.")
        return mat_khau


# ============================================================
#  SẢN PHẨM  ← MỚI
# ============================================================
class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = ['MaSP', 'Ten', 'Image', 'DanhMuc', 'MieuTa', 'TrangThai', 'Gia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Khoá mã sản phẩm khi chỉnh sửa để không thể đổi PK
            self.fields['MaSP'].disabled = True

    def clean_MaSP(self):
        ma_sp = self.cleaned_data.get('MaSP')
        if not self.instance.pk:
            if SanPham.objects.filter(MaSP=ma_sp).exists():
                raise forms.ValidationError("Mã sản phẩm này đã tồn tại trong hệ thống.")
        return ma_sp

    def clean_Ten(self):
        ten = self.cleaned_data.get('Ten', '').strip()
        if not ten:
            raise forms.ValidationError("Tên sản phẩm không được để trống.")
        return ten

    def clean_Gia(self):
        gia = self.cleaned_data.get('Gia')
        if gia is not None and gia < 0:
            raise forms.ValidationError("Giá bán không được là số âm.")
        return gia

    def clean_Image(self):
        image = self.cleaned_data.get('Image')
        # Chỉ kiểm tra khi người dùng upload ảnh mới (không phải giữ ảnh cũ)
        if image and hasattr(image, 'name'):
            # Kiểm tra định dạng file
            allowed_ext = ['.jpg', '.jpeg', '.png', '.webp']
            import os
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in allowed_ext:
                raise forms.ValidationError(
                    f"Định dạng ảnh không hợp lệ '{ext}'. Chỉ chấp nhận: JPG, PNG, WEBP.")
            # Kiểm tra dung lượng tối đa 5MB
            max_size = 5 * 1024 * 1024  # 5MB
            if image.size > max_size:
                size_mb = round(image.size / (1024 * 1024), 2)
                raise forms.ValidationError(
                    f"Ảnh quá lớn ({size_mb} MB). Dung lượng tối đa cho phép là 5MB.")
        return image


# ============================================================
#  DANH MỤC  ← MỚI
# ============================================================
class DanhMucForm(forms.ModelForm):
    class Meta:
        model = DanhMuc
        fields = ['MaDM', 'Ten']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['MaDM'].disabled = True

    def clean_MaDM(self):
        ma_dm = self.cleaned_data.get('MaDM')
        if not self.instance.pk:
            if DanhMuc.objects.filter(MaDM=ma_dm).exists():
                raise forms.ValidationError("Mã danh mục này đã tồn tại trong hệ thống.")
        return ma_dm

    def clean_Ten(self):
        ten = self.cleaned_data.get('Ten', '').strip()
        if not ten:
            raise forms.ValidationError("Tên danh mục không được để trống.")
        qs = DanhMuc.objects.filter(Ten__iexact=ten)
        if self.instance.pk:
            qs = qs.exclude(MaDM=self.instance.MaDM)
        if qs.exists():
            raise forms.ValidationError("Tên danh mục này đã tồn tại.")
        return ten


# ============================================================
#  TỒN KHO  ← MỚI
# ============================================================
class HangTonKhoForm(forms.ModelForm):
    class Meta:
        model = HangTonKho
        fields = ['MaKho', 'MaSP', 'SoLuong']

    def clean_SoLuong(self):
        sl = self.cleaned_data.get('SoLuong')
        if sl is not None and sl < 0:
            raise forms.ValidationError("Số lượng tồn kho không được là số âm.")
        return sl

    def clean(self):
        cleaned_data = super().clean()
        makho = cleaned_data.get('MaKho')
        masp = cleaned_data.get('MaSP')
        # Khi TẠO MỚI: kiểm tra trùng (MaKho, MaSP)
        if not self.instance.pk and makho and masp:
            if HangTonKho.objects.filter(MaKho=makho, MaSP=masp).exists():
                raise forms.ValidationError(
                    f"Đã tồn tại bản ghi tồn kho cho sản phẩm '{masp}' tại kho '{makho}'. "
                    "Vui lòng chỉnh sửa bản ghi hiện có thay vì tạo mới."
                )
        return cleaned_data


# ============================================================
#  NHẬP KHO  ← ĐÃ TĂNG CƯỜNG VALIDATION
# ============================================================
class YeuCauNhapKhoForm(forms.ModelForm):
    class Meta:
        model = YeuCauNhapKho
        fields = ['MaYC', 'Ngay', 'TrangThai', 'GhiChu']
        widgets = {
            'Ngay': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['MaYC'].disabled = True

    def clean_MaYC(self):
        ma_yc = self.cleaned_data.get('MaYC')
        if not self.instance.pk:
            if YeuCauNhapKho.objects.filter(MaYC=ma_yc).exists():
                raise forms.ValidationError("Mã yêu cầu nhập kho này đã tồn tại.")
        return ma_yc


# ============================================================
#  XUẤT KHO  ← ĐÃ TĂNG CƯỜNG VALIDATION
# ============================================================
class YeuCauXuatKhoForm(forms.ModelForm):
    class Meta:
        model = YeuCauXuatKho
        fields = ['MaPX', 'LyDo', 'DonHang', 'TrangThai', 'GhiChu']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['MaPX'].disabled = True

    def clean_MaPX(self):
        ma_px = self.cleaned_data.get('MaPX')
        if not self.instance.pk:
            if YeuCauXuatKho.objects.filter(MaPX=ma_px).exists():
                raise forms.ValidationError("Mã phiếu xuất kho này đã tồn tại.")
        return ma_px

