# views.py
from django.db import models
from django.db.models import Count, Sum, Avg, Q, FloatField, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os

from .models import Business
from .forms import BusinessReportForm, REPORT_FIELDS
from .utils.reporting import queryset_to_pdf


# --------------------------
# 1️⃣ Regular HTML business list
# --------------------------
def business_list(request):
    """Regular HTML view listing businesses."""
    businesses = Business.objects.all()
    return render(request, 'registry/business_list.html', {
        'businesses': businesses
    })


# --------------------------
# 2️⃣ Generic Businesses PDF Report
# --------------------------
@login_required
def businesses_report(request):
    """
    Unified PDF report view: handles default, date-range, and activity_code filters.
    Columns selection works for all filters.
    """
    form = BusinessReportForm(request.GET or None)

    # Optimize queryset
    queryset = Business.objects.select_related("activity_code", "profession", "assigned_clerk")

    # Default selected columns
    selected_columns = [f[0] for f in REPORT_FIELDS]

    if form.is_valid():
        # Filters
        status = form.cleaned_data.get("status")
        city = form.cleaned_data.get("city")
        activity_code = form.cleaned_data.get("activity_code")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

        if status:
            queryset = queryset.filter(status=status)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if activity_code:
            queryset = queryset.filter(activity_code=activity_code)
        if date_from:
            queryset = queryset.filter(date_registered__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_registered__lte=date_to)

        # Columns selection
        selected_columns = form.cleaned_data.get("columns") or selected_columns

        # Sorting
        sort_field = form.cleaned_data.get("sort_by")
        if sort_field:
            queryset = queryset.order_by(sort_field)

    # ----------------------------
    # Summary statistics
    # ----------------------------
    summary = queryset.aggregate(
        total_businesses=Count("id"),
        active_businesses=Count("id", filter=Q(status="active")),
        inactive_businesses=Count("id", filter=Q(status="inactive")),
        vat_registered=Count("id", filter=Q(is_vat_registered=True)),
        total_employees=Coalesce(Sum("number_of_employees"), 0, output_field=IntegerField()),
        avg_employees=Coalesce(Avg("number_of_employees"), 0.0, output_field=FloatField()),
    )

    # ----------------------------
    # Generate PDF if requested
    # ----------------------------
    if "generate" in request.GET:
        logo_path = os.path.join(
            settings.BASE_DIR, "registry", "static", "registry", "images", "city_logo.png"
        )
        return queryset_to_pdf(
            queryset=queryset,
            user=request.user,
            fields=selected_columns,
            title="Lista obrta",
            logo_path=logo_path,
            summary=summary,
        )

    # Default HTML page with summary and filter form
    return render(request, "registry/business_report_form.html", {
        "form": form,
        "summary": summary,
    })


# --------------------------
# 3️⃣ Activity Code PDF Report
# --------------------------
@login_required
def business_activity_report(request):
    """
    Report: Count businesses by primary activity and industry.
    Supports columns selection via the same BusinessReportForm.
    """
    form = BusinessReportForm(request.GET or None)
    queryset = Business.objects.select_related("activity_code", "profession")

    selected_columns = ["Activity Code", "Total Businesses"]  # default for this report

    if form.is_valid():
        # Filters
        status = form.cleaned_data.get("status")
        city = form.cleaned_data.get("city")
        activity_code_filter = form.cleaned_data.get("activity_code")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

        if status:
            queryset = queryset.filter(status=status)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if activity_code_filter:
            queryset = queryset.filter(activity_code=activity_code_filter)
        if date_from:
            queryset = queryset.filter(date_registered__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_registered__lte=date_to)

        # Columns selection
        form_columns = form.cleaned_data.get("columns")
        if form_columns:
            selected_columns = form_columns

    # Count by activity
    activity_counts = queryset.values("activity_code__code", "activity_code__description") \
                             .annotate(total=Count("id")) \
                             .order_by("activity_code__code")

    # Map to temporary objects for PDF
    class SimpleObj:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    pdf_qs = []
    for act in activity_counts:
        row = {}
        row["Activity Code"] = f"{act['activity_code__code']} - {act['activity_code__description']}"
        row["Total Businesses"] = act["total"]
        # Only include selected columns
        row = {k: v for k, v in row.items() if k in selected_columns}
        pdf_qs.append(SimpleObj(**row))

    # Generate PDF
    logo_path = os.path.join(settings.BASE_DIR, "registry", "static", "registry", "images", "city_logo.png")
    return queryset_to_pdf(
        queryset=pdf_qs,
        user=request.user,
        fields=selected_columns,
        title="Activity Code Report",
        logo_path=logo_path,
    )