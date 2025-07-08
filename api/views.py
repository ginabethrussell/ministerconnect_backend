from django.shortcuts import render
from rest_framework import generics
from .models import Church
from django.contrib.auth import get_user_model
from .serializers import ChurchSerializer, UserCreateSerializer

User = get_user_model()

class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

class ChurchCreateAPIView(generics.CreateAPIView):
    queryset = Church.objects.all()
    serializer_class = ChurchSerializer
