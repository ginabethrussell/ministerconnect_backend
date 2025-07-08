import re
from rest_framework import serializers
from .models import Church, US_STATE_CHOICES

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