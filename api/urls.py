from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import ChurchCreateAPIView, UserCreateAPIView

urlpatterns = [
    path('churches/create/', ChurchCreateAPIView.as_view(), name='church-create'),
    path('users/create/', UserCreateAPIView.as_view(), name='user-create'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 