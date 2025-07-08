from django.urls import path
from .views import ChurchCreateAPIView, UserCreateAPIView

urlpatterns = [
    path('churches/create/', ChurchCreateAPIView.as_view(), name='church-create'),
    path('users/create/', UserCreateAPIView.as_view(), name='user-create'),
] 