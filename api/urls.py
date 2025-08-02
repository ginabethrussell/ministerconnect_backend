from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    ApprovedCandidateViewSet,
    CandidateRegistrationAPIView,
    ChurchViewSet,
    InviteCodeViewSet,
    JobViewSet,
    MutualInterestViewSet,
    ProfileMeUpdateAPIView,
    ProfileResetAPIView,
    ProfileListAPIView,
    ResetPasswordAPIView,
    UpdateProfileStatusView,
    UpdateJobStatusView,
    UserMeAPIView,
    UserViewSet,
)


router = DefaultRouter()
router.register(
    r"approved-candidates", ApprovedCandidateViewSet, basename="approved-candidates"
)
router.register(r"churches", ChurchViewSet, basename="church")
router.register(r"invite-codes", InviteCodeViewSet, basename="invitecode")
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"mutual-interests", MutualInterestViewSet, basename="mutual-interest")
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "candidates/register/",
        CandidateRegistrationAPIView.as_view(),
        name="candidate-register",
    ),
    path(
        "jobs/<int:pk>/review/",
        UpdateJobStatusView.as_view(),
        name="update-job-status",
    ),
    path("profiles/", ProfileListAPIView.as_view(), name="profile-list"),
    path(
        "profiles/<int:pk>/review/",
        UpdateProfileStatusView.as_view(),
        name="update-profile-status",
    ),
    path("profile/me/", ProfileMeUpdateAPIView.as_view(), name="profile-me"),
    path("profile/reset/", ProfileResetAPIView.as_view(), name="profile-reset"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("user/me/", UserMeAPIView.as_view(), name="user-me"),
]
