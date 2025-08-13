from datetime import timezone

from django.db import models
from django.conf import settings
from PIL import Image
import os


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ add this
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)  # ✅ Add this

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            image_path = self.image.path
            img = Image.open(image_path)

            # Resize and crop to 800x400
            img = img.convert('RGB')  # Ensures it's in proper mode
            img.thumbnail((800, 400))  # Resize (preserving aspect ratio)
            img.save(image_path)


    def __str__(self):
        return self.title

class TicketType(models.Model):
    event = models.ForeignKey(Event, related_name="ticket_types", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, choices=[
        ('VIP', 'VIP'),
        ('REG', 'Regular'),
        ('GROUP', 'Group')
    ])  # e.g. Early Bird, VIP
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.event.title}"