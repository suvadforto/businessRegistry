# registry/forms.py
from django import forms
from .models import Business, ActivityCode

STATUS_CHOICES = [
    ('active', 'Active'),
    ('inactive', 'Inactive'),
]

class BusinessReportForm(forms.Form):
    status = forms.ChoiceField(choices=[('', 'All')] + STATUS_CHOICES, required=False)
    city = forms.CharField(max_length=50, required=False)
    activity_code = forms.ModelChoiceField(queryset=ActivityCode.objects.all(), required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))