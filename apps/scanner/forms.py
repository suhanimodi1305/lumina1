from django import forms

class ScanUploadForm(forms.Form):
    scan_image = forms.ImageField(label='Upload Photo')