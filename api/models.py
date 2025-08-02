from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from storages.backends.s3boto3 import S3Boto3Storage


if settings.DEBUG:
    file_storage = None
else:
    file_storage = S3Boto3Storage()

US_STATE_CHOICES = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
]

STATUS_CHOICES = [("active", "Active"), ("inactive", "Inactive")]

USER_STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("pending", "Pending"),
]

INVITE_CODE_STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("expired", "Expired"),
]

class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    church_id = models.ForeignKey(
        "Church", null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES)
    requires_password_change = models.BooleanField(default=False)
    invite_code = models.ForeignKey(
        "InviteCode", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

class Church(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=13)
    website = models.URLField()
    street_address = models.TextField()
    city = models.CharField()
    state = models.CharField(max_length=2, choices=US_STATE_CHOICES)
    zipcode = models.CharField(max_length=12)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                Lower("city"),
                "state",
                name="unique_church_name_city_state",
            )
        ]
        verbose_name_plural = "Churches"

    def __str__(self):
        return self.name

class InviteCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    event = models.CharField(max_length=255)
    used_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10, choices=INVITE_CODE_STATUS_CHOICES, default="active"
    )
    created_by = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="invite_codes"
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.event})"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    invite_code = models.ForeignKey(
        "InviteCode", on_delete=models.SET_NULL, null=True, blank=True
    )
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zipcode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
    )
    resume = models.FileField(
        upload_to="resumes/", storage=file_storage, null=True, blank=True
    )
    profile_image = models.ImageField(
        upload_to="profile-images/", storage=file_storage, null=True, blank=True
    )
    video_url = models.URLField(null=True, blank=True)
    placement_preferences = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"

    @classmethod
    def reset_to_draft(cls, user, invite_code):
        """
        Reset a user's profile to initial draft state.
        Deletes existing profile and its resume file, then creates a fresh one with only basic fields.
        """
        # Delete existing profile and its resume file and profile image files if they exist
        existing = cls.objects.filter(user=user)
        if existing.exists():
            old_profile = existing.first()
            if old_profile.resume:
                old_profile.resume.delete(save=False)
            if old_profile.profile_image:
                old_profile.profile_image.delete(save=False)
            old_profile.delete()

        # Create fresh profile with initial state
        return cls.objects.create(
            user=user,
            invite_code=invite_code,
            status="draft",
            street_address="",  # Required field, set to empty string
            city="",  # Required field, set to empty string
            state="",  # Required field, set to empty string
            zipcode="",  # Required field, set to empty string
            resume=None,  # Remove file reference from DB
        )

class Job(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    church = models.ForeignKey("Church", on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    ministry_type = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=100)
    job_description = models.TextField()
    about_church = models.TextField()
    job_url_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} at {self.church.name}"

class MutualInterest(models.Model):
    EXPRESSOR_CHOICES = [
        ("candidate", "Candidate"),
        ("church", "Church"),
    ]
    job_listing = models.ForeignKey(
        "Job", on_delete=models.CASCADE, related_name="mutual_interests"
    )
    profile = models.ForeignKey(
        "Profile", on_delete=models.CASCADE, related_name="mutual_interests"
    )
    expressed_by = models.CharField(max_length=10, choices=EXPRESSOR_CHOICES)
    expressed_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expressed_mutual_interests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job_listing", "profile", "expressed_by"],
                name="unique_interest_per_side",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.expressed_by.title()} → Profile {self.profile_id} / Job {self.job_listing_id}"

    @property
    def is_mutual(self):
        """Return True if both candidate and church have expressed interest for the same job/profile pair."""
        return (
            MutualInterest.objects.filter(
                job_listing=self.job_listing, profile=self.profile
            ).count()
            == 2
        )
