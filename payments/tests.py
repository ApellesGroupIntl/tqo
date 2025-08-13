from django.test import TestCase

# Create your tests here.
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tqo.settings')
django.setup()

from payments.mpesa import lipa_na_mpesa

try:
    response = lipa_na_mpesa(
        phone_number='254712345678',  # Test number
        amount=10,
        account_reference='TEST123',
        transaction_desc='Test payment',
        callback_url='https://example.com/callback'
    )
    print("API Response:", response)
except Exception as e:
    print("Error:", str(e))