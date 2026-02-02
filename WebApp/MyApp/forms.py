from django import forms

class YeuCauNhapKhoForm(forms.Form):
    san_pham = forms.CharField(label="Sản phẩm")
    so_luong = forms.IntegerField(label="Số lượng")
