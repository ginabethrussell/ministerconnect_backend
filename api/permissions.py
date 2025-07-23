from rest_framework.permissions import BasePermission

class IsInAnyGroup(BasePermission):
    def __init__(self, *group_names):
        self.group_names = group_names

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.groups.filter(name__in=self.group_names).exists()
        )

class IsAdminOrChurch(IsInAnyGroup):
    def __init__(self):
        super().__init__('Admin', 'Church User')
