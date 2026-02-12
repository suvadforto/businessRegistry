class RoleBasedAdminMixin:
    def _is_admin(self, request):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_authenticated and
            (
                request.user.is_superuser or
                request.user.role in ('admin', 'clerk', 'viewer')
            )
        )

    def has_add_permission(self, request):
        return self._is_admin(request) or request.user.role == 'clerk'

    def has_change_permission(self, request, obj=None):
        return self._is_admin(request) or request.user.role == 'clerk'

    def has_delete_permission(self, request, obj=None):
        return self._is_admin(request)

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if self.has_view_permission(request) else qs.none()

    def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser or request.user.role == 'admin':
        return self.readonly_fields

    if request.user.role == 'viewer':
        return [f.name for f in self.model._meta.fields]

    return self.readonly_fields



