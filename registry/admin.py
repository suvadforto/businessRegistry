from registry.utils.pdf import businesses_to_pdf
from django.core.exceptions import ValidationError
from django import forms
from django.urls import path
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.admin.widgets import AutocompleteSelectMultiple
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
    User,
    AuditLog,
    ActivityCode,
)

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


class BusinessAdminForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        activity_code = cleaned_data.get("activity_code")
        secondary = cleaned_data.get("secondary_activities")

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
    list_display = ('name', 'registration_number', 'status','business_type', 'industry','date_registered', 'is_deleted' )
    search_fields = ('name', 'registration_number', 'tax_number')
    list_filter = ('status', 'city', 'legal_form', 'assigned_clerk', 'business_type',)
    autocomplete_fields = ('activity_code', 'assigned_clerk')
    filter_horizontal=('secondary_activities',)
    ordering = ('name',)
#NEW fieldsets 12.02.2026    
    fieldsets = (
    ('Osnovni Podaci', {
        'fields': ('name', 'registration_number', 'tax_number', 'status', 'date_registered')
    }),
    ('Klasifikacija', {
        'fields': ('industry', 'business_type','legal_form', 'activity_code','secondary_activities')
    }),
    ('Operativni Podaci', {
        'fields': ('start_date', 'end_date', 'number_of_employees')
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
    inlines = [BusinessOwnerInline, LicenseInline, InspectionInline, DocumentInline]
    actions = ['mark_inactive', 'mark_active', 'print_selected_pdf', 'restore_records',]     
        
        
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
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('activity_code', 'assigned_clerk')
    
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

    def get_actions(self, request):
        actions = super().get_actions(request)

    # Only admins/superusers can restore
        if not (request.user.is_superuser or request.user.role == 'admin'):
            actions.pop('restore_records', None)

        return actions
        
    
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




