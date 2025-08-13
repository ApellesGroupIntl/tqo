from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.username', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'location',
            'date',
            'time',
            'price',
            'organizer',
            'organizer_name',
        ]
        read_only_fields = ['organizer']
