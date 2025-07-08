import re
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import Church, US_STATE_CHOICES

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    groups = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'password', 'groups', 'church_id', 'status', 'requires_password_change'
        ]

    def validate_church(self, value):
      if value is None:
          return value  # Allow null if your model allows it
      if not Church.objects.filter(pk=value.id).exists():
          raise serializers.ValidationError("The specified church does not exist.")
      return value

    def create(self, validated_data):
      group_names = validated_data.pop('groups', [])
      password = validated_data.pop('password')
      validated_data['username'] = validated_data['email']
      user = User(**validated_data)
      user.set_password(password)
      user.save()
      for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
      return user

class ChurchSerializer(serializers.ModelSerializer):
    def validate(self, data):
        name = data['name'].strip().lower()
        city = data['city'].strip().lower()
        state = data['state'].upper()
        if Church.objects.filter(
            name__iexact=data['name'].strip(),
            city__iexact=data['city'].strip(),
            state=state
        ).exists():
            raise serializers.ValidationError("A church with this name, city, and state already exists.")
        return data

    def create(self, validated_data):
        validated_data['name'] = validated_data['name'].strip().title()
        validated_data['city'] = validated_data['city'].strip().title()
        return super().create(validated_data)

    def validate_state(self, value):
        valid_states = dict(US_STATE_CHOICES)
        if value.upper() not in valid_states:
            raise serializers.ValidationError("State must be a valid US 2-letter abbreviation.")
        return value.upper()
    
    def validate_phone(self, value):
        if not re.match(r'^\+?1?\d{10,13}$', value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_zipcode(self, value):
        if not re.match(r'^\d{5}(-\d{4})?$', value):
            raise serializers.ValidationError("Enter a valid US ZIP code.")
        return value

    class Meta:
        model = Church
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'website',
            'street_address',
            'city',
            'state',
            'zipcode',
            'status',
            'created_at',
            'updated_at',
        ] 