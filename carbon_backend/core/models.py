from django.db import models
from django.utils import timezone


class SystemConfig(models.Model):
    """Model for storing system-wide configuration settings."""
    
    name = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_value(cls, name, default=None):
        """Get a configuration value by name."""
        try:
            config = cls.objects.get(name=name, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default
