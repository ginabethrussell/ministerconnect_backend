from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    ChurchViewSet,
    UserViewSet,
    InviteCodeViewSet,
    CandidateRegistrationAPIView,
    UserMeAPIView,
    ResetPasswordAPIView,
    ProfileMeUpdateAPIView,
    ProfileResetAPIView,
    ProfileListAPIView,
    UpdateProfileStatusView,
    UpdateJobStatusView,
    JobViewSet,
    MutualInterestViewSet,
    ApprovedCandidateViewSet,
)

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"mutual-interests", MutualInterestViewSet, basename="mutual-interest")
router.register(r"churches", ChurchViewSet, basename="church")
router.register(
    r"approved-candidates", ApprovedCandidateViewSet, basename="approved-candidates"
)
router.register(r"invite-codes", InviteCodeViewSet, basename="invitecode")
router.register(r"users", UserViewSet)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "candidates/register/",
        CandidateRegistrationAPIView.as_view(),
        name="candidate-register",
    ),
    path("user/me/", UserMeAPIView.as_view(), name="user-me"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("profile/me/", ProfileMeUpdateAPIView.as_view(), name="profile-me"),
    path("profile/reset/", ProfileResetAPIView.as_view(), name="profile-reset"),
    path("profiles/", ProfileListAPIView.as_view(), name="profile-list"),
    path(
        "profiles/<int:pk>/review/",
        UpdateProfileStatusView.as_view(),
        name="update-profile-status",
    ),
    path(
        "jobs/<int:pk>/review/",
        UpdateJobStatusView.as_view(),
        name="update-job-status",
    ),
    path("", include(router.urls)),
]
