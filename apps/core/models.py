from django.db import models

class ProviderConfig(models.Model):
    # Explicit manager to satisfy linters and provide query interface
    objects = models.Manager()

    name = models.CharField(max_length=100, unique=True)
    field_selectors = models.JSONField(
        help_text="JSON mapping of field names to CSS selectors or XPath expressions"
    )

    def __str__(self):
        return str(self.name)