#admin.py
from django.contrib.admin import site
from django.http import JsonResponse

from django.db.models import Count
from django.contrib.admin import ChoicesFieldListFilter
from django.contrib import messages
from django.contrib.admin.widgets import AutocompleteSelect
from registry.utils.pdf import businesses_to_pdf
from django.core.exceptions import ValidationError
from django import forms
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
#from django.contrib.admin.widgets import AutocompleteSelectMultiple
from django.conf import settings
import os
from django.utils.timezone import now
#from .utils.pdf import render_pdf
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Business,
    Owner,
    BusinessOwner,
    License,
    Inspection,
    Document,
    Assessment,
    User,
    AuditLog,
    ActivityCode,
    Profession,
)

def business_stats(request):
    if not request.user.is_authenticated:
        raise PermissionDenied

    data = (
        Business.objects
        .values('industry')
        .annotate(count=Count('id'))
    )

    labels = []
    counts = []

    for item in data:
        labels.append(item['industry'])
        counts.append(item['count'])

    return JsonResponse({
        "labels": labels,
        "data": counts
    })


def business_status_stats(request):
    if not request.user.is_authenticated:
        raise PermissionDenied

    data = (
        Business.objects
        .values('status')
        .annotate(count=Count('id'))
    )

    labels = []
    counts = []

    for item in data:
        labels.append(item['status'])
        counts.append(item['count'])

    return JsonResponse({
        "labels": labels,
        "data": counts
    })

# -------------------------
# SOFT DELETE ADMIN MIXIN
# -------------------------

class SoftDeleteAdminMixin:
    def get_queryset(self, request):
        # IMPORTANT: use all_objects if available
        if hasattr(self.model, 'all_objects'):
            qs = self.model.all_objects.all()
        else:
            qs = super().get_queryset(request)

        # Admins see everything
        if request.user.is_superuser or request.user.role == 'admin':
            return qs

        # Others see only active
        return qs.filter(is_deleted=False)

    def delete_model(self, request, obj):
        obj.soft_delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()



# -------------------------
# ROLE-BASED ADMIN MIXIN
# -------------------------
class RoleBasedAdminMixin:
    """
    Handles role-based permissions and read-only fields.
    """

    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_authenticated and
            request.user.role in ('admin', 'clerk', 'viewer')
        )

    def has_add_permission(self, request):
        return request.user.role in ('admin', 'clerk')

    def has_change_permission(self, request, obj=None):
        return request.user.role in ('admin', 'clerk')

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def get_readonly_fields(self, request, obj=None):
        readonly = []

        # Viewer sees everything read-only
        if request.user.role == 'viewer':
            readonly = [f.name for f in self.model._meta.fields]

        # Non-editable fields like created_at/updated_at are always read-only
        readonly += [f.name for f in self.model._meta.fields if not f.editable]

        return readonly

    def has_module_permission(self, request):
        return self.has_view_permission(request)


# -------------------------
# INLINE MODELS
# -------------------------
class BusinessOwnerInline(admin.TabularInline):
    model = BusinessOwner
    extra = 1
    autocomplete_fields = ['owner']


class LicenseInline(admin.TabularInline):
    model = License
    verbose_name = "Dozvola"
    verbose_name_plural = "Dozvole"
    extra = 0
    fields = ('license_type', 'license_number', 'issue_date', 'expiry_date', 'status')
    show_change_link = True


class InspectionInline(admin.TabularInline):
    model = Inspection
    extra = 0
    fields = ('inspection_date', 'inspector_name', 'result')
    show_change_link = True

class AssessmentInline(admin.TabularInline):
    model = Assessment
    extra = 0
    fields = ('document_number', 'assessment_date', 'result', 'document_file', 'file_link')
    readonly_fields = ('file_link',)

    def file_link(self, obj):
        if obj.document_file:
            return format_html('<a href="{}" target="_blank">Pregled</a>', obj.document_file.url)
        return "-"

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    readonly_fields = ('uploaded_at',)
    show_change_link = True

@admin.register(ActivityCode)
class ActivityCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')
    ordering = ('code',)
@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')
    ordering = ('code',)


class WideAutocompleteSelect(AutocompleteSelect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({'style': 'width:400px;'})  # adjust width as needed


##################################################################


class BusinessAdminForm(forms.ModelForm):

    class Meta:
        model = Business
        fields = "__all__"
        widgets = {
            'activity_code': forms.Select(attrs={'style': 'width: 400px;'}),
            'profession': forms.Select(attrs={'style': 'width: 400px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['secondary_activities'].widget.attrs.update({'size': '15'})

    def clean(self):
        cleaned_data = super().clean()

        industry = cleaned_data.get("industry")
        obrt_type = cleaned_data.get("obrt_type")

        activity_code = cleaned_data.get("activity_code")
        secondary = cleaned_data.get("secondary_activities")
        end_date = cleaned_data.get("end_date")
        ending_registration_number = cleaned_data.get("ending_registration_number")
        if end_date and not ending_registration_number:
            self.add_error(
                "ending_registration_number",
                "Unesite broj rješenja o prestanku ako je datum prestanka definisan."
            )
            
        if industry == "obrt" and not obrt_type:
            self.add_error(
                "obrt_type",
                "Morate odabrati vrstu obrta."
            )

        if industry != "obrt":
            cleaned_data["obrt_type"] = None

        if activity_code and secondary and activity_code in secondary:
            self.add_error(
                "secondary_activities",
                "Glavna djelatnost ne može biti među dodatnim djelatnostima."
            )

        return cleaned_data





# -------------------------
# BUSINESS ADMIN
# -------------------------
@admin.register(Business)
class BusinessAdmin(RoleBasedAdminMixin,SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ('owner_name','name', 'registration_number', 'status','business_type', 'industry','date_registered', 'is_deleted')
    list_per_page = 25          # how many items per page
    list_max_show_all = 100     # limit for "Show all"
    show_full_result_count = False 
    
    search_fields = ('name', 'registration_number', 'tax_number','ownerships__owner__first_name',
    'ownerships__owner__last_name','ownerships__owner__personal_id',)
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset.distinct(), True
    list_filter = ('status', ('industry', ChoicesFieldListFilter), 'business_type', 'profession', 'assigned_clerk', )
    autocomplete_fields = ('activity_code', 'assigned_clerk', 'profession')
    filter_horizontal=('secondary_activities',)
    ordering = ('name',)
#NEW fieldsets 12.02.2026    
    fieldsets = (
    ('Osnovni Podaci', {
        'fields': ('name', 'registration_number', 'date_registered', 'status','tax_number' )
    }),
    ('Klasifikacija', {
        'fields': ('industry', 'obrt_type','business_type', 'profession', 'activity_code','secondary_activities','is_foreign_trade',)
    }),
    ('Operativni Podaci', {
        'fields': ('start_date', 'end_date', 'ending_registration_number','number_of_employees')
    }),
    ('Finansije i Porezi', {
        'fields': ('is_vat_registered', 'bank_account')
    }),
    ('Kontakt Podaci', {
        'fields': ('address', 'city', 'postal_code', 'phone', 'email')
    }),
    ('Napomene', {
        'fields': ('notes', 'internal_notes')
    })
#    ('Sistemska Polja', {
#        'fields': ('created_at', 'updated_at')
#    }),
    )
    form = BusinessAdminForm
    class Media:
        js = (
                'admin/js/vendor/jquery/jquery.js',
                '/admin/jsi18n/',  # 👈 important
                'admin/js/obrt_toggle.js',
                
                'admin/js/obrt_toggle.js',              # then your custom script
            )
            
        
    inlines = [BusinessOwnerInline, LicenseInline, InspectionInline, AssessmentInline, DocumentInline]
    actions = ['mark_inactive', 'mark_active', 'print_selected_pdf', 'restore_records',]     
    
    def owner_name(self, obj):
        owner_rel = obj.ownerships.first()
        if owner_rel and owner_rel.owner:
            return f"{owner_rel.owner.last_name} {owner_rel.owner.first_name}"
        return "-"
    
    owner_name.short_description = "Vlasnik"    
    owner_name.admin_order_field = 'ownerships__owner__last_name'
    @admin.action(description="Označi odabrane obrte kao Neaktivan")
    def mark_inactive(self, request, queryset):
        queryset.update(status='inactive')

    @admin.action(description="Označi odabrane obrte kao Aktivan")
    def mark_active(self, request, queryset):
        queryset.update(status='active')
    @admin.action(description="Štampaj odabrane obrte (PDF)")
    def print_selected_pdf(self, request, queryset):
        if not queryset.exists():
            self.message_user(
                request,
                "Molimo odaberite najmanje jedan obrt.",
                level="warning",
            )
            return

        return businesses_to_pdf(queryset, request.user)
#    def get_queryset(self, request):
#        qs = super().get_queryset(request)
#        return qs.select_related('activity_code', 'assigned_clerk')
               
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('activity_code', 'assigned_clerk')\
                 .prefetch_related('ownerships__owner')   
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'        
    @admin.action(description="Povrati odabrane podatke obrta")
    def restore_records(self, request, queryset):
        restored = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                restored += 1

        self.message_user(
            request,
            f"{restored} business(es) restored successfully."
        )
#    def export_pdf_link(self, obj):
#        return format_html(
#            '<a href="/businesses/report/" target="_blank">PDF</a>'
#        )
#    export_pdf_link.short_description = "Export PDF"
#    list_display = ('name', 'registration_number', 'status', 'export_pdf_link')
    def get_actions(self, request):
        actions = super().get_actions(request)

    # Only admins/superusers can restore
        if not (request.user.is_superuser or request.user.role == 'admin'):
            actions.pop('restore_records', None)

        return actions
    def response_add(self, request, obj, post_url_continue=None):
        response = super().response_add(request, obj, post_url_continue)

        # Clear default Django message
        storage = messages.get_messages(request)
        for _ in storage:
            pass

        # Add Bosnian message
        messages.success(request, f'Obrt "{obj.name}" je uspješno dodan.')

        return response


    def response_change(self, request, obj):
        response = super().response_change(request, obj)

        # Clear default Django message
        storage = messages.get_messages(request)
        for _ in storage:
            pass

        # Add Bosnian message
        messages.success(request, f'Obrt "{obj.name}" je uspješno izmijenjen.')

        return response    
# -------------------------
# OWNER ADMIN
# -------------------------
@admin.register(Owner)
class OwnerAdmin(RoleBasedAdminMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'personal_id', 'phone')
    search_fields = ('first_name', 'last_name', 'personal_id')
    ordering = ('last_name', 'first_name')


# -------------------------
# LICENSE ADMIN
# -------------------------
@admin.register(License)
class LicenseAdmin(RoleBasedAdminMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ('license_type', 'license_number', 'business', 'status', 'expiry_date')
    list_filter = ('status', 'license_type')
    search_fields = ('license_number', 'business__name')
    autocomplete_fields = ('business',)


# -------------------------
# INSPECTION ADMIN
# -------------------------
@admin.register(Inspection)
class InspectionAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = ('business', 'inspection_date', 'inspector_name', 'result')
    list_filter = ('result',)
    autocomplete_fields = ('business',)

#assessment admin
@admin.register(Assessment)
class AssessmentAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = ('business', 'document_number', 'assessment_date', 'result')
    list_filter = ('result',)
    autocomplete_fields = ('business',)

# -------------------------
# DOCUMENT ADMIN
# -------------------------
@admin.register(Document)
class DocumentAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = ('document_type', 'business', 'uploaded_at')
    search_fields = ('document_type', 'business__name')
    autocomplete_fields = ('business',)


# -------------------------
# USER ADMIN (superuser bypasses role)
# -------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (('Registry Role', {'fields': ('role',)}),)
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'


# -------------------------
# AUDIT LOG ADMIN (READ-ONLY)
# -------------------------
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'table_name', 'record_id', 'user', 'action_time')
    list_filter = ('action', 'table_name')
    readonly_fields = ('user', 'action', 'table_name', 'record_id', 'action_time')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def dashboard_data(request):

    if not request.user.is_authenticated:
        raise PermissionDenied

    businesses = Business.objects.all().values(
        "industry",
        "status",
        "date_registered"
    )

    return JsonResponse(list(businesses), safe=False)


admin_urls = [
    path("dashboard-data/", admin.site.admin_view(dashboard_data)),
    path("business-stats/", admin.site.admin_view(business_stats)),
    path("business-status-stats/", admin.site.admin_view(business_status_stats)),
]

admin.site.get_urls = (lambda original: lambda: admin_urls + original())(admin.site.get_urls)