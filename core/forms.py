from django import forms

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
