from django import forms
from .models import YeuCauNhapKho, YeuCauXuatKho, DanhGiaCuaHang 
class YeuCauNhapKhoForm(forms.ModelForm):
    class Meta:
        model = YeuCauNhapKho
        fields = ['MaYC', 'Ngay', 'TrangThai', 'GhiChu', 'MaNV']
        widgets = {
            'Ngay': forms.DateInput(attrs={'type': 'date'}),
        }

class YeuCauXuatKhoForm(forms.ModelForm):
    class Meta:
        model = YeuCauXuatKho
        fields = ['MaPX', 'LyDo', 'DonHang', 'TrangThai', 'GhiChu', 'MaNV']

class DanhGiaForm(forms.ModelForm):
    class Meta:
        model = DanhGiaCuaHang
        # Sửa tên trường ở đây cho khớp với Model mới
        fields = ['Diem', 'BinhLuan'] 
        widgets = {
            'Diem': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '5', 
                'placeholder': 'Nhập số từ 1 đến 5'
            }),
            'BinhLuan': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Cửa hàng này thế nào? Chia sẻ trải nghiệm của bạn nhé...'
            }),
        }