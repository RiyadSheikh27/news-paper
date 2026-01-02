from django.db import models

"""Start of utils/models.py"""
class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True