# mpesa/models.py

from django.db import models
from django.conf import settings
from events.models import Event

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,                   # allow guest payments
        blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=50, unique=True, null=True)
    checkout_request_id = models.CharField(max_length=50, unique=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ticket = models.FileField(upload_to='tickets/', null=True, blank=True)
    status_message = models.TextField(blank=True)
    amount_integer = models.IntegerField(null=True, blank=True)  # 🔹 CHANGE: ensure raw integer amount is stored

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.status}"
