import re
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import serializers
from .models import Church, US_STATE_CHOICES, InviteCode, MutualInterest, Profile, Job

User = get_user_model()

logger = logging.getLogger(__name__)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    groups = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    invite_code = serializers.PrimaryKeyRelatedField(
        queryset=InviteCode.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
            "password",
            "groups",
            "church_id",
            "status",
            "requires_password_change",
            "invite_code",
        ]
        read_only_fields = ["name"]

    def validate_church(self, value):
        if value is None:
            return value  # Allow null if your model allows it
        if not Church.objects.filter(pk=value.id).exists():
            raise serializers.ValidationError("The specified church does not exist.")
        return value

    def validate_email(self, value):
        return value.strip().lower()

    def validate_first_name(self, value):
        return value.strip().title()

    def validate_last_name(self, value):
        return value.strip().title()

    def create(self, validated_data):
        group_names = validated_data.pop("groups", [])
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "").strip().title()
        last_name = validated_data.pop("last_name", "").strip().title()
        full_name = f"{first_name} {last_name}".strip()
        validated_data["first_name"] = first_name
        validated_data["last_name"] = last_name
        validated_data["name"] = full_name
        validated_data["username"] = validated_data["email"]
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return user


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
            "church_id",
            "status",
            "requires_password_change",
            "groups",
        ]
        read_only_fields = ["email", "name", "church_id"]

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]


class ResetPasswordSerializer(serializers.Serializer):
    temporary_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["temporary_password"] == data["new_password"]:
            raise serializers.ValidationError(
                "New password must be different from the current password."
            )
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError(
                "New password must be at least 8 characters long."
            )
        return data


class ChurchSerializer(serializers.ModelSerializer):
    users = UserCreateSerializer(many=True, required=False, write_only=True)

    def validate(self, data):
        name = data.get("name")
        city = data.get("city")
        state = data.get("state")

        # Only run duplicate check if all 3 are present
        if name and city and state:
            normalized_name = name.strip().lower()
            normalized_city = city.strip().lower()
            normalized_state = state.upper()

            # Exclude self on update
            existing = Church.objects.filter(
                name__iexact=normalized_name,
                city__iexact=normalized_city,
                state=normalized_state,
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise serializers.ValidationError(
                    "A church with this name, city, and state already exists."
                )

        return data

    def create(self, validated_data):
        users_data = validated_data.pop("users", [])
        validated_data["name"] = validated_data["name"].strip().title()
        validated_data["city"] = validated_data["city"].strip().title()

        with transaction.atomic():
            church = super().create(validated_data)

            for user_data in users_data:
                user_data["church_id"] = church.id  # assign church foreign key
                serializer = UserCreateSerializer(data=user_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        return church

    def validate_state(self, value):
        valid_states = dict(US_STATE_CHOICES)
        if value.upper() not in valid_states:
            raise serializers.ValidationError(
                "State must be a valid US 2-letter abbreviation."
            )
        return value.upper()

    def validate_phone(self, value):
        if not re.match(r"^\+?1?\d{10,13}$", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_zipcode(self, value):
        if not re.match(r"^\d{5}(-\d{4})?$", value):
            raise serializers.ValidationError("Enter a valid US ZIP code.")
        return value

    def update(self, instance, validated_data):
        users_data = validated_data.pop("users", [])

        # Normalize church fields
        if "name" in validated_data:
            validated_data["name"] = validated_data["name"].strip().title()
        if "city" in validated_data:
            validated_data["city"] = validated_data["city"].strip().title()

        # Update church fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle user create or update
        for user_data in users_data:
            user_data["church_id"] = instance.id  # assign FK

            user_id = user_data.get("id")
            if user_id:
                # Update existing user
                try:
                    user = User.objects.get(id=user_id, church_id=instance.id)
                except User.DoesNotExist:
                    raise serializers.ValidationError(
                        f"User with id {user_id} not found in this church."
                    )

                serializer = UserCreateSerializer(user, data=user_data, partial=True)
            else:
                # Create new user
                serializer = UserCreateSerializer(data=user_data)

            serializer.is_valid(raise_exception=True)
            serializer.save()

        return instance

    class Meta:
        model = Church
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "website",
            "street_address",
            "city",
            "state",
            "zipcode",
            "status",
            "created_at",
            "updated_at",
            "users",
        ]
        read_only_fields = ["created_at", "updated_at"]


class InviteCodeSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InviteCode
        fields = [
            "id",
            "code",
            "event",
            "used_count",
            "status",
            "created_by",
            "created_by_name",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        return obj.created_by.name if obj.created_by else None


class CandidateRegistrationSerializer(serializers.Serializer):
    invite_code = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    def validate_invite_code(self, value):
        try:
            invite = InviteCode.objects.get(code=value)
        except InviteCode.DoesNotExist:
            raise serializers.ValidationError("Invite code does not exist.")
        if invite.status != "active":
            raise serializers.ValidationError("Invite code is not active.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        invite = InviteCode.objects.get(code=validated_data["invite_code"])
        invite.used_count += 1
        invite.save()
        first_name = validated_data["first_name"].strip().title()
        last_name = validated_data["last_name"].strip().title()
        full_name = f"{first_name} {last_name}"
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            name=full_name,
            status="active",
            is_active=True,
            invite_code=invite,  # Assign invite_code foreign key
        )
        group, _ = Group.objects.get_or_create(name="Candidate")
        user.groups.add(group)
        user.save()
        # --- Create draft profile ---
        Profile.objects.create(user=user, invite_code=invite, status="draft")
        return user


class UserMeSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField(read_only=True)
    invite_code = serializers.PrimaryKeyRelatedField(read_only=True)
    invite_code_string = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "name",
            "church_id",
            "status",
            "requires_password_change",
            "created_at",
            "updated_at",
            "groups",
            "invite_code",
            "invite_code_string",
        ]
        read_only_fields = fields

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def get_invite_code_string(self, obj):
        return obj.invite_code.code if obj.invite_code else None


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class ProfileSerializer(serializers.ModelSerializer):
    invite_code_string = serializers.SerializerMethodField(read_only=True)
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = [
            "user",
            "invite_code",
            "created_at",
            "updated_at",
            "invite_code_string",
        ]

    def get_invite_code_string(self, obj):
        return obj.invite_code.code if obj.invite_code else None

    def validate(self, data):
        # Only enforce required fields if status is 'pending'
        status = data.get("status") or getattr(self.instance, "status", None)
        if status == "pending":
            required_fields = [
                "phone",
                "street_address",
                "city",
                "state",
                "zipcode",
                "resume",
            ]
            missing = [
                field
                for field in required_fields
                if not data.get(field)
                and not (self.instance and getattr(self.instance, field, None))
            ]
            if missing:
                raise serializers.ValidationError(
                    {field: "This field is required." for field in missing}
                )
        return data

    def update(self, instance, validated_data):
        new_image = validated_data.get("profile_image", None)
        if new_image and instance.profile_image and instance.profile_image != new_image:
            instance.profile_image.delete(save=False)  # delete old image from S3

        new_resume = validated_data.get("resume", None)
        if new_resume and instance.resume and instance.resume != new_resume:
            instance.resume.delete(save=False)  # delete old resume from S3

        return super().update(instance, validated_data)


class ProfileResetSerializer(serializers.Serializer):
    """
    Serializer for resetting a profile to draft state.
    No input fields required - just calls the model method.
    """

    def create(self, validated_data):
        user = self.context["request"].user
        invite_code = user.invite_code
        return Profile.reset_to_draft(user, invite_code)


class ProfileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "status"]
        read_only_fields = ["id"]


class ChurchInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Church
        fields = [
            "id",
            "name",
            "website",
            "city",
            "state",
        ]


class JobSerializer(serializers.ModelSerializer):
    church = ChurchInlineSerializer(read_only=True)

    class Meta:
        model = Job
        fields = "__all__"

    def create(self, validated_data):
        validated_data["status"] = "pending"  # force pending on create
        return super().create(validated_data)


class JobStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id", "status"]
        read_only_fields = ["id"]


class MutualInterestSerializer(serializers.ModelSerializer):
    is_mutual = serializers.SerializerMethodField()
    church_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="job_listing.title", read_only=True)
    candidate_name = serializers.SerializerMethodField()

    class Meta:
        model = MutualInterest
        fields = [
            "id",
            "job_listing",
            "job_title",
            "church_name",
            "profile",
            "candidate_name",
            "expressed_by",
            "expressed_by_user",
            "created_at",
            "updated_at",
            "is_mutual",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "expressed_by_user",
            "is_mutual",
        ]

    def get_is_mutual(self, obj):
        return obj.is_mutual

    def create(self, validated_data):
        validated_data["expressed_by_user"] = self.context["request"].user
        return super().create(validated_data)

    def get_church_name(self, obj):
        return (
            obj.job_listing.church.name
            if obj.job_listing and obj.job_listing.church
            else None
        )

    def get_candidate_name(self, obj):
        return obj.profile.user.name if obj.profile and obj.profile.user else None
