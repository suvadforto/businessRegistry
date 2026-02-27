# registry/forms.py
from django.conf import settings
from django import forms
from .models import Business, ActivityCode
import datetime

STATUS_CHOICES = [
    ('active', 'Aktivan'),
    ('inactive', 'Neaktivan'),
]

REPORT_FIELDS = [
    ('name', 'Naziv'),
    ('registration_number', 'Broj rješenja'),
    ('city', 'Grad'),
    ('status', 'Status'),
    ('industry', 'Vrsta djelatnosti'),
    ('number_of_employees', 'Broj zaposlenih'),
    ('is_vat_registered', 'PDV obveznik'),
    ('activity_code', 'Djelatnost'),
    ('date_registered', 'Datum registracije'),
    ('end_date', 'Datum zatvaranja'),
    ('profession', 'Zanimanje'),
]

SORT_FIELDS = [
    ('name', 'Naziv'),
    ('registration_number', 'Matični broj'),
    ('city', 'Grad'),
    ('status', 'Status'),
]


class BusinessReportForm(forms.Form):
    
    status = forms.ChoiceField(
        choices=[('', 'Svi')] + STATUS_CHOICES,
        required=False
    )
    city = forms.CharField(
        max_length=50,
        required=False,
        label="Grad"
    )
    activity_code = forms.ModelChoiceField(
        queryset=ActivityCode.objects.all(),
        required=False,
        label="Šifra djelatnosti"
    )

    # -------------------------------
    # Bosnian-friendly date inputs
    # -------------------------------
    date_from = forms.DateField(
    required=False,
    input_formats=["%Y-%m-%d"],  # keeps current working browser format
    widget=forms.DateInput(attrs={
        'type': 'date',  # important, so browser handles it
        'min': '1995-01-01',
        'max': datetime.date.today().strftime('%Y-%m-%d'),
    }),
    label="Datum od"
    )

    date_to = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': '1995-01-01',
            'max': datetime.date.today().strftime('%Y-%m-%d'),
        }),
        label="Datum do"
    )

    columns = forms.MultipleChoiceField(
        choices=REPORT_FIELDS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Odaberi polja u izvještaju"
    )

    sort_by = forms.ChoiceField(
        choices=[('', 'Bez sortiranja')] + SORT_FIELDS,
        required=False,
        label="Sortiraj po"
    )

    # -------------------------------
    # Validation for date range
    # -------------------------------
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            self.add_error("date_to", "Dan zatvaranja ne može biti ranije od datuma početka.")

        return cleaned_data