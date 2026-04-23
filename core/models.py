from django.db import models
import uuid6
from django.core.validators import MinValueValidator, MaxValueValidator


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    name = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=10)
    gender_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    age = models.PositiveIntegerField()
    age_group = models.CharField(max_length=20)
    country_id = models.CharField(max_length=2)
    country_name = models.CharField(max_length=255, null=True, blank=True)
    country_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["gender"]),
            models.Index(fields=["age_group"]),
            models.Index(fields=["country_id"]),
            models.Index(fields=["age"]),
        ]

    def __str__(self):
        return self.name
