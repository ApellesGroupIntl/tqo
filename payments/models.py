from django.db import models
from django.conf import settings
from events.models import Event

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=50, unique=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    ticket = models.FileField(upload_to='tickets/', null=True, blank=True)
    amount_integer = models.IntegerField()  # For M-Pesa transactions


    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.status}"