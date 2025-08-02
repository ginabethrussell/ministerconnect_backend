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
        super().__init__("Admin", "Church User")

    def has_object_permission(self, request, view, obj):
        if request.user.groups.filter(name="Admin").exists():
            return True
        if request.user.groups.filter(name="Church User").exists():
            user_church_id = getattr(
                request.user.church_id, "id", None
            )  # ← unwrap Church instance
            obj_church_id = getattr(obj, "church_id", None)
            return obj_church_id == user_church_id
        return False


class IsAdmin(IsInAnyGroup):
    def __init__(self):
        super().__init__("Admin")


class IsChurchUser(IsInAnyGroup):
    def __init__(self):
        super().__init__("Church User")
