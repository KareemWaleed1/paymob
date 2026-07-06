from rest_framework.permissions import BasePermission


class IsMerchantUser(BasePermission):
    message = "Authenticated user is not linked to a merchant."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "merchant")
        )
