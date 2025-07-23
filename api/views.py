from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from .models import Church, InviteCode, Job, Profile, MutualInterest
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    ChurchSerializer,
    JobSerializer,
    UserCreateSerializer,
    InviteCodeSerializer,
    CandidateRegistrationSerializer,
    UserMeSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ProfileResetSerializer,
    ProfileStatusSerializer,
    MutualInterestSerializer,
)
from rest_framework.views import APIView
from .permissions import IsAdmin, IsAdminOrChurch


User = get_user_model()


class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]


class ChurchCreateAPIView(generics.CreateAPIView):
    queryset = Church.objects.all()
    serializer_class = ChurchSerializer
    permission_classes = [IsAuthenticated]


class InviteCodeCreateAPIView(generics.CreateAPIView):
    queryset = InviteCode.objects.all()
    serializer_class = InviteCodeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InviteCodeListAPIView(generics.ListAPIView):
    queryset = InviteCode.objects.all()
    serializer_class = InviteCodeSerializer
    permission_classes = [IsAuthenticated]


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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "church", "ministry_type", "employment_type"]


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
        url_path="matches",
        permission_classes=[IsAuthenticated],
    )
    def mutual_matches(self, request):
        user = request.user

        if not user.church_id:
            return Response([], status=403)

        # Optional filter by job_listing
        job_filter = request.query_params.get("job_listing")

        # Get all jobs tied to this user's church
        job_ids = user.church_id.jobs.values_list("id", flat=True)

        if job_filter:
            try:
                job_filter = int(job_filter)
            except ValueError:
                return Response({"detail": "Invalid job_listing ID."}, status=400)
            if job_filter not in job_ids:
                return Response(
                    {"detail": "Job not found or not associated with your church."},
                    status=404,
                )
            job_ids = [job_filter]

        # Find (job, profile) pairs with 2 interest expressions (candidate + church)
        mutual_pairs = (
            MutualInterest.objects.filter(job_listing_id__in=job_ids)
            .values("job_listing_id", "profile_id")
            .annotate(match_count=Count("id"))
            .filter(match_count=2)
        )

        matches = [
            (pair["job_listing_id"], pair["profile_id"]) for pair in mutual_pairs
        ]

        # Return only church expressions from this user for mutual matches
        mutual_qs = MutualInterest.objects.filter(
            expressed_by="church",
            job_listing_id__in=[j for j, _ in matches],
            profile_id__in=[p for _, p in matches],
            expressed_by_user=user,
        ).select_related("job_listing", "profile")

        serializer = self.get_serializer(mutual_qs, many=True)
        return Response(serializer.data)

    from rest_framework.permissions import IsAdminUser

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
