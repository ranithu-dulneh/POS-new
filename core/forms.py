from django import forms
from .models import Product

class POSForm(forms.Form):
    barcode = forms.CharField(
        label='Enter Barcode or Product Code',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'autofocus': 'autofocus',
            'placeholder': 'Scan barcode...'
        })
    )

class ManagerLoginForm(forms.Form):
    code = forms.CharField(
        label='Protection Code',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'barcode', 'product_code', 'price', 'stock_quantity', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AddStockForm(forms.Form):
    quantity = forms.IntegerField(
        label='Purchasing (Add Quantity)',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
