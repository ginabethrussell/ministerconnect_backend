from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

US_STATE_CHOICES = [
    ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
    ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
    ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
    ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
    ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
    ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
    ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
    ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
    ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
    ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
    ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
    ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'), ('WY', 'Wyoming'),
]

STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]

USER_STATUS_CHOICES = [
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('pending', 'Pending'),
]

INVITE_CODE_STATUS_CHOICES = [
    ('active', 'Active'),
    ('expired', 'Expired'),
]

class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    church_id = models.ForeignKey('Church', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')
    status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES)
    requires_password_change = models.BooleanField(default=False)
    # last_login is already included in AbstractUser
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username is still required by AbstractUser

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
                Lower('name'), Lower('city'), 'state',
                name='unique_church_name_city_state'
            )
        ]
        verbose_name_plural = "Churches"

    def __str__(self):
        return self.name

class InviteCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    event = models.CharField(max_length=255)
    used_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=INVITE_CODE_STATUS_CHOICES, default='active')
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='invite_codes')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.event})"
