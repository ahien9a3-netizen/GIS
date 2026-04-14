from django import forms
from .models import YeuCauNhapKho

class YeuCauNhapKhoForm(forms.ModelForm):
    class Meta:
        model = YeuCauNhapKho
        fields = ['MaYC', 'Ngay', 'TrangThai', 'GhiChu', 'MaNV']
        widgets = {
            'Ngay': forms.DateInput(attrs={'type': 'date'}),
        }

from .models import DanhGiaCuaHang

class DanhGiaForm(forms.ModelForm):
    class Meta:
        model = DanhGiaCuaHang
        fields = ['SoSao', 'NhanXet']
        widgets = {
            'SoSao': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '5', 
                'placeholder': 'Nhập số từ 1 đến 5'
            }),
            'NhanXet': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Cửa hàng này thế nào? Chia sẻ trải nghiệm của bạn nhé...'
            }),
        }