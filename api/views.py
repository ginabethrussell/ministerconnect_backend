import logging
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import generics, status
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
)
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

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
        logger.warning(f"GET ProfileMeAPIView - DEBUG: {settings.DEBUG}")
        logger.warning(f"GET ProfileMeAPIView - DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
        logger.warning(f"GET ProfileMeAPIView - Storage backend in use: {default_storage.__class__}")
        logger.warning(f"GET ProfileMeAPIView - AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
        
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

    def get_object(self):
        # Log the storage backend in use
        logger.warning(f"GET ProfileMeUpdateAPIView - DEBUG: {settings.DEBUG}")
        logger.warning(f"GET ProfileMeUpdateAPIView - DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
        logger.warning(f"GET ProfileMeUpdateAPIView - Storage backend in use: {default_storage.__class__}")
        logger.warning(f"GET ProfileMeUpdateAPIView - AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        logger.warning(f"UPDATE ProfileMeUpdateAPIView - Request.FILES: {request.FILES}")
        logger.warning(f"UPDATE ProfileMeUpdateAPIView - DEBUG: {settings.DEBUG}")
        logger.warning(f"UPDATE ProfileMeUpdateAPIView - DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
        logger.warning(f"UPDATE ProfileMeUpdateAPIView - Storage backend in use: {default_storage.__class__}")
        logger.warning(f"UPDATE ProfileMeUpdateAPIView - AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
        
        # Log the actual storage backend being used for file uploads
        if request.FILES:
            for field_name, uploaded_file in request.FILES.items():
                logger.warning(f"UPDATE ProfileMeUpdateAPIView - File '{field_name}': {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        return super().update(request, *args, **kwargs)
