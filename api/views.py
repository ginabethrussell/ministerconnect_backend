from django.shortcuts import render
from rest_framework import generics
from .models import Church
from .serializers import ChurchSerializer

# Create your views here.

class ChurchCreateAPIView(generics.CreateAPIView):
    queryset = Church.objects.all()
    serializer_class = ChurchSerializer
