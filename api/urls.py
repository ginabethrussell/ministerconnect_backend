from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    ChurchCreateAPIView,
    UserCreateAPIView,
    InviteCodeCreateAPIView,
    InviteCodeListAPIView,
    CandidateRegistrationAPIView,
    UserMeAPIView,
    ResetPasswordAPIView,
    ProfileMeUpdateAPIView,
    ProfileResetAPIView,
    ProfileListAPIView,
    UpdateProfileStatusView,
)

urlpatterns = [
    path("churches/create/", ChurchCreateAPIView.as_view(), name="church-create"),
    path("users/create/", UserCreateAPIView.as_view(), name="user-create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "invite-codes/create/",
        InviteCodeCreateAPIView.as_view(),
        name="invite-code-create",
    ),
    path("invite-codes/", InviteCodeListAPIView.as_view(), name="invite-code-list"),
    path(
        "candidates/register/",
        CandidateRegistrationAPIView.as_view(),
        name="candidate-register",
    ),
    path("user/me/", UserMeAPIView.as_view(), name="user-me"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("profile/me/", ProfileMeUpdateAPIView.as_view(), name="profile-me"),
    path("profile/reset/", ProfileResetAPIView.as_view(), name="profile-reset"),
    path('profiles/', ProfileListAPIView.as_view(), name='profile-list'),
    path('profiles/<int:pk>/status/', UpdateProfileStatusView.as_view(), name='update-profile-status'),
]
