# registry/forms.py
from django.conf import settings
from django import forms
from .models import Business, ActivityCode, Profession, Owner
import datetime


STATUS_CHOICES = [
    ('active', 'Aktivan'),
    ('inactive', 'Neaktivan'),
]
GROUP_BY_CHOICES = [
    ("", "Bez grupisanja"),
    ('ownerships__owner__sex', 'Spol vlasnika'),
    #("city", "Grad"),
    ("industry", "Vrsta djelatnosti"),
    ("status", "Status"),
]



REPORT_FIELDS = [
    ('owner_full_name', 'Vlasnik'),
    ('name', 'Naziv'),
    ('owner_sex', 'Spol vlasnika'),
    ('assessment_result', 'Procjena uslova'),
    ('registration_number', 'Broj rješenja'),
    #('city', 'Grad'),
    ('status', 'Status'),
    ('industry', 'Vrsta djelatnosti'),
    ('activity_code', 'Glavna djelatnost'),
    ('profession', 'Zanimanje'),
    ('date_registered', 'Datum registracije'),
    ('number_of_employees', 'Broj zaposlenih'),
    ('is_vat_registered', 'PDV obveznik'),  
    ('end_date', 'Datum zatvaranja'),
    
]

SORT_FIELDS = [
    ('name', 'Naziv'),
    ('owner_full_name', 'Vlasnik'),
    ('registration_number', 'Matični broj'),
    ('city', 'Grad'),
    ('status', 'Status'),
]


class BusinessReportForm(forms.Form):
    
    SEX_CHOICES = [
    ('', '--- Svi ---'),
    ('M', 'Muški'),
    ('F', 'Ženski'),
    ]

    sex = forms.ChoiceField(
        choices=SEX_CHOICES,
        required=False,
        label="Spol vlasnika"
    )
    
    
    status = forms.ChoiceField(
        choices=[('', 'Svi')] + STATUS_CHOICES,
        required=False
    )
    
    industry = forms.ChoiceField(
        choices=[('', 'Sve')] + list(Business._meta.get_field('industry').choices),
        required=False,
        label="Vrsta djelatnosti"
    )
    city = forms.CharField(
        max_length=50,
        required=False,
        label="Grad"
    )
    profession = forms.ModelChoiceField(
        queryset=Profession.objects.all(),
        required=False,
        label="Zanimanje"
    )
    activity_code = forms.ModelChoiceField(
        queryset=ActivityCode.objects.all(),
        required=False,
        label="Šifra djelatnosti"
    )
    group_by = forms.ChoiceField(
    choices=GROUP_BY_CHOICES,
    required=False,
    label="Grupiši po"
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