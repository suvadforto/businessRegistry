from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os

from .models import Business, ActivityCode
from .forms import BusinessReportForm
from .utils.reporting import queryset_to_pdf


def business_list(request):
    """Regular HTML view listing businesses."""
    businesses = Business.objects.all()
    return render(request, 'registry/business_list.html', {
        'businesses': businesses
    })


@login_required
def businesses_report(request):
    """
    Dynamic PDF report view for Businesses.
    Users can filter by status, city, activity_code, and registration date range.
    """
    form = BusinessReportForm(request.GET or None)
    queryset = Business.objects.all()

    # Apply filters if form is valid
    if form.is_valid():
        if form.cleaned_data.get("status"):
            queryset = queryset.filter(status=form.cleaned_data["status"])
        if form.cleaned_data.get("city"):
            queryset = queryset.filter(city__icontains=form.cleaned_data["city"])
        if form.cleaned_data.get("activity_code"):
            queryset = queryset.filter(activity_code=form.cleaned_data["activity_code"])
        if form.cleaned_data.get("date_from"):
            queryset = queryset.filter(date_registered__gte=form.cleaned_data["date_from"])
        if form.cleaned_data.get("date_to"):
            queryset = queryset.filter(date_registered__lte=form.cleaned_data["date_to"])

    # If user clicked "Generate PDF", create the report
    if "generate" in request.GET:
        logo_path = os.path.join(
            settings.BASE_DIR, "registry", "static", "registry", "images", "city_logo.png"
        )

        return queryset_to_pdf(
            queryset=queryset,
            user=request.user,
            fields=[
                "name",
                "registration_number",
                "city",
                "status",
                "industry",
                "number_of_employees",
                "is_vat_registered",
                "activity_code",
            ],
            title="Lista obrta",
            logo_path=logo_path
        )

    # Otherwise, render the filter form
    return render(request, "registry/business_report_form.html", {
        "form": form
    })