from rest_framework import serializers, viewsets
from .models import Business

# Convert Business objects to JSON
class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'  # or list fields you want publicly visible

# Define a viewset for REST API
class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
