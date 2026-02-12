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
)
from .admin_permissions import RoleBasedAdminMixin

# -------------------------
# INLINES
# -------------------------

class BusinessOwnerInline(admin.TabularInline):
    model = BusinessOwner
    extra = 1
    autocomplete_fields = ['owner']


class LicenseInline(admin.TabularInline):
    model = License
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


# -------------------------
# BUSINESS ADMIN
# -------------------------

@admin.register(Business)
class BusinessAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'registration_number',
        'city',
        'status',
        'date_registered',
    )

    search_fields = (
        'name',
        'registration_number',
        'tax_number',
    )

    list_filter = (
        'status',
        'city',
        'legal_form',
    )

    ordering = ('name',)

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'registration_number',
                'tax_number',
                'status',
                'date_registered',
            )
        }),
        ('Business Details', {
            'fields': (
                'industry',
                'legal_form',
                'notes',
            )
        }),
        ('Contact Information', {
            'fields': (
                'address',
                'city',
                'postal_code',
                'phone',
                'email',
            )
        }),
        ('System Fields', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    inlines = [
        BusinessOwnerInline,
        LicenseInline,
        InspectionInline,
        DocumentInline,
    ]

    autocomplete_fields = []

    actions = ['mark_inactive', 'mark_active']

    @admin.action(description="Mark selected businesses as inactive")
    def mark_inactive(self, request, queryset):
        queryset.update(status='inactive')

    @admin.action(description="Mark selected businesses as active")
    def mark_active(self, request, queryset):
        queryset.update(status='active')


# -------------------------
# OWNER ADMIN
# -------------------------

@admin.register(Owner)
class OwnerAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'personal_id', 'phone')
    search_fields = ('first_name', 'last_name', 'personal_id')
    ordering = ('last_name', 'first_name')


# -------------------------
# LICENSE ADMIN
# -------------------------

@admin.register(License)
class LicenseAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = (
        'license_type',
        'license_number',
        'business',
        'status',
        'expiry_date',
    )
    list_filter = ('status', 'license_type')
    search_fields = ('license_number', 'business__name')
    autocomplete_fields = ('business',)


# -------------------------
# INSPECTION ADMIN
# -------------------------

@admin.register(Inspection)
class InspectionAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = (
        'business',
        'inspection_date',
        'inspector_name',
        'result',
    )
    list_filter = ('result',)
    autocomplete_fields = ('business',)


# -------------------------
# DOCUMENT ADMIN
# -------------------------

@admin.register(Document)
class DocumentAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    list_display = (
        'document_type',
        'business',
        'uploaded_at',
    )
    search_fields = ('document_type', 'business__name')
    readonly_fields = ('uploaded_at',)
    autocomplete_fields = ('business',)


# -------------------------
# USER ADMIN (with roles)
# -------------------------
        
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Registry Role', {
            'fields': ('role',),
        }),
    )

    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

    def has_view_permission(self, request, obj=None):
        # superuser bypasses role
        return request.user.is_superuser or request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'


# -------------------------
# AUDIT LOG (READ ONLY)
# -------------------------

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'action',
        'table_name',
        'record_id',
        'user',
        'action_time',
    )
    list_filter = ('action', 'table_name')
    readonly_fields = (
        'user',
        'action',
        'table_name',
        'record_id',
        'action_time',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
