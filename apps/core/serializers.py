from rest_framework import serializers
from .models import ProviderConfig

class ProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderConfig
        fields = ['id', 'name', 'field_selectors']
        read_only_fields = ['id']