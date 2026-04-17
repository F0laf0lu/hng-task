from django.db import models
import uuid
import uuid6    
from django.core.validators import MinValueValidator, MaxValueValidator



class Profile(models.Model):
    id = models.UUIDField(primary_key=True, 
                          default=uuid6.uuid7, editable=False)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    gender_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    sample_size = models.IntegerField()
    age = models.PositiveIntegerField()
    age_group = models.CharField(max_length=255)
    country_id = models.CharField(max_length=255)
    country_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    created_at = models.DateTimeField(auto_now_add=True)