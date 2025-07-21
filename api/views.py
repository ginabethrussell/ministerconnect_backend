from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from .models import Church, InviteCode, Profile
from django.contrib.auth import get_user_model
from .serializers import (
    ChurchSerializer,
    UserCreateSerializer,
    InviteCodeSerializer,
    CandidateRegistrationSerializer,
    UserMeSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ProfileResetSerializer,
)
from rest_framework.views import APIView


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
