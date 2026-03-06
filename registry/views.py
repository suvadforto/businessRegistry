# views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, FloatField, IntegerField
from django.db.models.functions import Coalesce
from django.conf import settings
import os
import logging

from .models import Business
from .forms import BusinessReportForm, REPORT_FIELDS
from .utils.reporting import queryset_to_pdf


logger = logging.getLogger(__name__)


@login_required
def businesses_report(request):
    form = BusinessReportForm(request.GET or None)

    queryset = Business.objects.select_related(
        "activity_code",
        "profession",
        "assigned_clerk",
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
        industry = form.cleaned_data.get("industry")

        # -------------------------
        # Filtering
        # -------------------------

        if industry:
            queryset = queryset.filter(industry=industry)

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
    # Summary (always based on filtered queryset)
    # -------------------------

    summary = queryset.aggregate(
        total_businesses=Count("id"),
        active_businesses=Count("id", filter=Q(status="active")),
        inactive_businesses=Count("id", filter=Q(status="inactive")),
        vat_registered=Count("id", filter=Q(is_vat_registered=True)),
        total_employees=Coalesce(
            Sum("number_of_employees"),
            0,
            output_field=IntegerField()
        ),
        avg_employees=Coalesce(
            Avg("number_of_employees"),
            0.0,
            output_field=FloatField()
        ),
    )

    # -------------------------
    # Generate PDF
    # -------------------------

    if "generate" in request.GET:

        title = "Lista obrta"

        if form.is_valid():

            group_by = form.cleaned_data.get("group_by")
            date_from = form.cleaned_data.get("date_from")
            date_to = form.cleaned_data.get("date_to")

            # Show grouping in title
            if group_by:
                group_labels = dict(form.fields["group_by"].choices)
                group_label = group_labels.get(group_by)
                title += f"<br/>Grupisano po: {group_label}"

            filters = []

            # Status
            status = form.cleaned_data.get("status")
            if status:
                status_label = dict(Business.STATUS_CHOICES).get(status, status)
                filters.append(f"Status: {status_label}")

            # City
            city = form.cleaned_data.get("city")
            if city:
                filters.append(f"Grad: {city}")

            # Industry (ChoiceField label)
            industry = form.cleaned_data.get("industry")
            if industry:
                industry_label = dict(Business.INDUSTRY_CHOICES).get(industry, industry)
                filters.append(f"Vrsta djelatnosti: {industry_label}")

            # Activity code
            activity_code = form.cleaned_data.get("activity_code")
            if activity_code:
                filters.append(f"Šifra djelatnosti: {activity_code.code}")

            # Date range
            if date_from and date_to:
                filters.append(
                    f"Period: {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}"
                )
            elif date_from:
                filters.append(f"Od: {date_from.strftime('%d.%m.%Y')}")
            elif date_to:
                filters.append(f"Do: {date_to.strftime('%d.%m.%Y')}")

            if filters:
                title += "<br/>" + "<br/>".join(filters)

        logo_path = os.path.join(
            settings.BASE_DIR,
            "registry",
            "static",
            "registry",
            "images",
            "city_logo.png",
        )

        return queryset_to_pdf(
            queryset=queryset,
            user=request.user,
            fields=selected_columns,
            title=title,
            logo_path=logo_path,
            summary=summary,
            grouped_data=grouped_data,
        )

    return render(
        request,
        "registry/business_report_form.html",
        {
            "form": form,
            "summary": summary,
        },
    )


@login_required
def business_activity_report(request):
    """
    PDF report: Count businesses by primary activity code.
    """

    form = BusinessReportForm(request.GET or None)

    queryset = Business.objects.select_related(
        "activity_code",
        "profession"
    )

    selected_columns = ["Activity Code", "Total Businesses"]

    if form.is_valid():

        status = form.cleaned_data.get("status")
        city = form.cleaned_data.get("city")
        activity_code_filter = form.cleaned_data.get("activity_code")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        industry_filter = form.cleaned_data.get("industry")

        if industry_filter:
            queryset = queryset.filter(industry=industry_filter)

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

    # -------------------------
    # Aggregate by activity code
    # -------------------------

    activity_counts = (
        queryset
        .values("activity_code__code", "activity_code__description")
        .annotate(total=Count("id"))
        .order_by("activity_code__code")
    )

    # Create simple objects for PDF

    class SimpleObj:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    pdf_qs = []

    for act in activity_counts:

        row = {
            "Activity Code": f"{act['activity_code__code']} - {act['activity_code__description']}",
            "Total Businesses": act["total"],
        }

        row = {k: v for k, v in row.items() if k in selected_columns}

        pdf_qs.append(SimpleObj(**row))

    logo_path = os.path.join(
        settings.BASE_DIR,
        "registry",
        "static",
        "registry",
        "images",
        "city_logo.png",
    )

    return queryset_to_pdf(
        queryset=pdf_qs,
        user=request.user,
        fields=selected_columns,
        title="Activity Code Report",
        logo_path=logo_path,
    )