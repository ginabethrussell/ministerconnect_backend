from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView
from .models import Church, InviteCode, Job, Profile, MutualInterest
from .permissions import IsChurchUser, IsAdmin, IsAdminOrChurch
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    ChurchSerializer,
    JobSerializer,
    JobStatusSerializer,
    UserCreateSerializer,
    UserSerializer,
    InviteCodeSerializer,
    CandidateRegistrationSerializer,
    UserMeSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ProfileResetSerializer,
    ProfileStatusSerializer,
    MutualInterestSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer  # swap with UserSerializer if you have one
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["church_id"]  # filter users by church via ?church_id=

    def get_queryset(self):
        queryset = super().get_queryset()

        # Optional: limit by current admin’s scope
        if self.request.user.groups.filter(name="Church User").exists():
            queryset = queryset.filter(church_id=self.request.user.church_id)

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "partial_update", "update"]:
            return UserSerializer
        return UserCreateSerializer


class ChurchViewSet(viewsets.ModelViewSet):
    queryset = Church.objects.all()
    serializer_class = ChurchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrChurch]

    def get_queryset(self):
        # Customize this if you want to filter by current user’s church only, etc.
        return Church.objects.all()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        church = self.get_object()
        users = church.user_set.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class ApprovedCandidateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsChurchUser]

    def get_queryset(self):
        return Profile.objects.select_related("user").filter(
            status="approved", user__is_active=True
        )


class InviteCodeViewSet(viewsets.ModelViewSet):
    queryset = InviteCode.objects.select_related("created_by").all()
    serializer_class = InviteCodeSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Invite codes cannot be deleted. Mark as 'inactive' or update expiration instead."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class CandidateRegistrationAPIView(generics.CreateAPIView):
    serializer_class = CandidateRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Registration successful. Please log in."},
            status=status.HTTP_201_CREATED,
        )


class UserMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class ResetPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        # Verify the temporary password
        if not user.check_password(serializer.validated_data["temporary_password"]):
            return Response(
                {"detail": "Temporary password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set the new password
        user.set_password(serializer.validated_data["new_password"])
        user.requires_password_change = False
        user.save()

        return Response(
            {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
        )


class ProfileListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrChurch]

    def get(self, request):
        status_param = request.query_params.get("status")

        profiles = Profile.objects.select_related("user").all()

        if status_param:
            profiles = profiles.filter(status=status_param)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(profiles, request)
        serializer = ProfileSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProfileMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)


class ProfileMeUpdateAPIView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # <-- Add this line

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        if request.FILES:
            for field_name, uploaded_file in request.FILES.items():
                pass
        return super().update(request, *args, **kwargs)


class ProfileResetAPIView(generics.CreateAPIView):
    """
    Reset the authenticated user's profile to draft state.
    This will delete all profile data and create a fresh draft profile.
    """

    serializer_class = ProfileResetSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            {
                "detail": "Profile reset to draft successfully.",
                "profile": ProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class UpdateProfileStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        serializer = ProfileStatusSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsAdminOrChurch]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "church", "ministry_type", "employment_type"]

    def perform_create(self, serializer):
        church = self.request.user.church_id
        serializer.save(church=church)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(
            request, instance
        )  # ✅ calls has_object_permission
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["get"],
        url_path="my-jobs",
        permission_classes=[IsAuthenticated, IsChurchUser],
    )
    def my_jobs(self, request):
        church_id = request.user.church_id.pk  # or request.user.church_id.pk
        if not church_id:
            return Response(
                {"detail": "You are not associated with a church."}, status=403
            )
        queryset = Job.objects.filter(church_id=church_id).order_by("-created_at")
        # Use the built-in paginator
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback if pagination fails
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UpdateJobStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        serializer = JobStatusSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MutualInterestViewSet(viewsets.ModelViewSet):
    queryset = MutualInterest.objects.all()
    serializer_class = MutualInterestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["job_listing", "profile", "expressed_by"]

    def get_queryset(self):
        return MutualInterest.objects.filter(expressed_by_user=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        url_path="my-church-interests",
        permission_classes=[IsAuthenticated, IsChurchUser],
    )
    def my_church_interests(self, request):
        church_id = getattr(request.user.church_id, "pk", None)
        if not church_id:
            return Response(
                {"detail": "You are not associated with a church."}, status=403
            )

        job_ids = Job.objects.filter(church_id=church_id).values_list("id", flat=True)
        interests = MutualInterest.objects.filter(job_listing_id__in=job_ids)

        # Paginate
        paginator = PageNumberPagination()
        paginated = paginator.paginate_queryset(interests, request)

        serializer = self.get_serializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="matches",
        permission_classes=[IsAuthenticated],
    )
    def mutual_matches(self, request):
        user = request.user

        # Ensure the user is associated with a church
        if not user.church_id:
            return Response([], status=status.HTTP_403_FORBIDDEN)

        # Get all job IDs belonging to the user's church
        job_ids = list(
            Job.objects.filter(church=user.church_id).values_list("id", flat=True)
        )

        # Optional filter: restrict to a specific job_listing
        job_filter = request.query_params.get("job_listing")
        if job_filter:
            try:
                job_filter = int(job_filter)
            except ValueError:
                return Response(
                    {"detail": "Invalid job_listing ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if job_filter not in job_ids:
                return Response(
                    {"detail": "Job not found or not associated with your church."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            job_ids = [job_filter]

        # Identify mutual pairs: candidate + church both expressed interest
        mutual_pairs = (
            MutualInterest.objects.filter(job_listing_id__in=job_ids)
            .values("job_listing_id", "profile_id")
            .annotate(match_count=Count("id"))
            .filter(match_count=2)
        )

        matches = [
            (pair["job_listing_id"], pair["profile_id"]) for pair in mutual_pairs
        ]

        # Return only the 'church' side of the mutual interest (to avoid duplicate records)
        mutual_qs = MutualInterest.objects.filter(
            expressed_by="church",
            expressed_by_user=user,
            job_listing_id__in=[j for j, _ in matches],
            profile_id__in=[p for _, p in matches],
        ).select_related("job_listing", "profile")

        # Apply pagination if enabled
        page = self.paginate_queryset(mutual_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback for non-paginated response
        serializer = self.get_serializer(mutual_qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-matches",
        permission_classes=[IsAuthenticated, IsAdmin],
    )
    def admin_matches(self, request):
        # Find all (job, profile) pairs that have both candidate + church expressions
        mutual_pairs = (
            MutualInterest.objects.values("job_listing_id", "profile_id")
            .annotate(match_count=Count("id"))
            .filter(match_count=2)
        )

        matches = [
            (pair["job_listing_id"], pair["profile_id"]) for pair in mutual_pairs
        ]

        # Return the church-side expression for each match
        mutual_qs = MutualInterest.objects.filter(
            expressed_by="church",
            job_listing_id__in=[j for j, _ in matches],
            profile_id__in=[p for _, p in matches],
        ).select_related("job_listing", "profile", "expressed_by_user")

        serializer = self.get_serializer(mutual_qs, many=True)
        return Response(serializer.data)
