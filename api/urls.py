from django.urls import path
from .views import ChurchCreateAPIView

urlpatterns = [
    path('churches/create/', ChurchCreateAPIView.as_view(), name='church-create'),
] 