# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, FloatField, IntegerField
from django.db.models.functions import Coalesce
from django.conf import settings
import os

from .models import Business
from .forms import BusinessReportForm, REPORT_FIELDS
from .utils.reporting import queryset_to_pdf



import logging

logger = logging.getLogger(__name__)  # Add this at the top of views.py

@login_required
@login_required
def businesses_report(request):
    form = BusinessReportForm(request.GET or None)

    queryset = Business.objects.select_related(
        "activity_code", "profession", "assigned_clerk"
    )

    selected_columns = [f[0] for f in REPORT_FIELDS]
    grouped_data = None
    

    if form.is_valid():

        status = form.cleaned_data.get("status")
        city = form.cleaned_data.get("city")
        activity_code = form.cleaned_data.get("activity_code")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        group_by = form.cleaned_data.get("group_by")

        # -------------------------
        # Filtering
        # -------------------------
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

        # -------------------------
        # Sorting
        # -------------------------
        sort_field = form.cleaned_data.get("sort_by")
        if sort_field:
            queryset = queryset.order_by(sort_field)

        # -------------------------
        # Column selection
        # -------------------------
        selected_columns = form.cleaned_data.get("columns") or selected_columns

        # -------------------------
        # Grouping
        # -------------------------
        if group_by:
            grouped_data = (
                queryset
                .values(group_by)
                .annotate(total=Count("id"))
                .order_by("-total")
            )

    # -------------------------
    # Summary (always computed on filtered queryset)
    # -------------------------
    summary = queryset.aggregate(
        total_businesses=Count("id"),
        active_businesses=Count("id", filter=Q(status="active")),
        inactive_businesses=Count("id", filter=Q(status="inactive")),
        vat_registered=Count("id", filter=Q(is_vat_registered=True)),
        total_employees=Coalesce(Sum("number_of_employees"), 0, output_field=IntegerField()),
        avg_employees=Coalesce(Avg("number_of_employees"), 0.0, output_field=FloatField()),
    )
    # -------------------------
    # Generate PDF
    # -------------------------
    if "generate" in request.GET:

        # Base title
        title = "Lista obrta"

        # Auto-adjust title if grouped
        if form.is_valid():
            group_by = form.cleaned_data.get("group_by")
            date_from = form.cleaned_data.get("date_from")
            date_to = form.cleaned_data.get("date_to")
            if group_by:
                group_labels = dict(form.fields["group_by"].choices)
                group_label = group_labels.get(group_by)
                title = f"Lista obrta – Grupisano po {group_label}"
             
             # -------------------------
    # Add date range to title
    # -------------------------
            if date_from and date_to:
                title += f" (Period: {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')})"
            elif date_from:
                title += f" (Od: {date_from.strftime('%d.%m.%Y')})"
            elif date_to:
                title += f" (Do: {date_to.strftime('%d.%m.%Y')})"
                
        logo_path = os.path.join(
            settings.BASE_DIR,
            "registry",
            "static",
            "registry",
            "images",
            "city_logo.png"
        )

        return queryset_to_pdf(
            queryset=queryset,
            user=request.user,
            fields=selected_columns,
            title=title,   # ✅ dynamic title
            logo_path=logo_path,
            summary=summary,
            grouped_data=grouped_data,
        )
   
    return render(request, "registry/business_report_form.html", {
        "form": form,
        "summary": summary,
    })


@login_required
def business_activity_report(request):
    """
    PDF report: Count businesses by primary activity code.
    Supports column selection via BusinessReportForm.
    """
    form = BusinessReportForm(request.GET or None)
    queryset = Business.objects.select_related("activity_code", "profession")

    selected_columns = ["Activity Code", "Total Businesses"]

    if form.is_valid():
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

        form_columns = form.cleaned_data.get("columns")
        if form_columns:
            selected_columns = form_columns

    # Aggregate businesses by activity_code
    activity_counts = queryset.values("activity_code__code", "activity_code__description") \
                             .annotate(total=Count("id")) \
                             .order_by("activity_code__code")

    # Create temporary objects for PDF generation
    class SimpleObj:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    pdf_qs = []
    for act in activity_counts:
        row = {}
        row["Activity Code"] = f"{act['activity_code__code']} - {act['activity_code__description']}"
        row["Total Businesses"] = act["total"]
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