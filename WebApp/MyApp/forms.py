from django import forms
from .models import YeuCauNhapKho, YeuCauXuatKho

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
