from django import forms
from .models import YeuCauNhapKho

class YeuCauNhapKhoForm(forms.ModelForm):
    class Meta:
        model = YeuCauNhapKho
        fields = ['MaYC', 'Ngay', 'TrangThai', 'GhiChu', 'MaNV']
        widgets = {
            'Ngay': forms.DateInput(attrs={'type': 'date'}),
        }
