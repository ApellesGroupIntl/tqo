# payments/mpesa.py
import base64
import requests
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def generate_password(shortcode, passkey, timestamp):
    """Generate M-Pesa API password using base64 encoding"""
    try:
        data_to_encode = f"{shortcode}{passkey}{timestamp}"
        return base64.b64encode(data_to_encode.encode()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error generating password: {str(e)}")
        raise


def get_access_token():
    """Get OAuth access token from M-Pesa API with better error handling"""
    try:
        auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(
            auth_url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            headers={'Content-Type': 'application/json'},
            timeout=3000
        )

        # Add detailed error logging
        logger.debug(f"Auth response: {response.status_code} - {response.text}")

        response.raise_for_status()
        data = response.json()

        if 'access_token' not in data:
            logger.error("No access_token in response")
            raise ValueError("Invalid token response")

        return data['access_token']

    except Exception as e:
        logger.error(f"Failed to get access token: {str(e)}")
        raise

def lipa_na_mpesa(phone_number, amount, account_reference, transaction_desc, callback_url):
    """Initiate STK push payment request with dynamic inputs"""
    try:
        if not all([phone_number, amount, account_reference, transaction_desc, callback_url]):
            raise ValueError("All parameters are required")

        amount = int(float(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive")

        access_token = get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = generate_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": "600998",  # use actual user phone
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": 254714441708,  # use actual user phone
            "CallBackURL": "https://europe-vbulletin-duo-powerpoint.trycloudflare.com/payments/initiate-stk-push/",
            # "CallBackURL": callback_url,   # use provided callback URL
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Debug: show exactly what's being sent
        logger.debug(f"STK Push Payload: {payload}")
        logger.debug(f"Headers: {headers}")

        stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        response = requests.post(stk_url, json=payload, headers=headers, timeout=3000)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"M-Pesa API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        raise ValueError("Failed to initiate payment. Please try again later.")
    except Exception as e:
        logger.error(f"Error in lipa_na_mpesa: {str(e)}")
        raise


access_token = get_access_token()
logger.debug(f"Access Token: {access_token}")


# def lipa_na_mpesa(phone_number, amount, account_reference, transaction_desc, callback_url):
#     """Initiate STK push payment request with comprehensive error handling"""
#     try:
#         # Validate inputs
#         if not all([phone_number, amount, account_reference, transaction_desc, callback_url]):
#             raise ValueError("All parameters are required")
#
#         # Convert amount to integer
#         try:
#             amount = int(float(amount))
#             if amount <= 0:
#                 raise ValueError("Amount must be positive")
#         except (ValueError, TypeError):
#             raise ValueError("Invalid amount format")
#
#         # Get access token
#         access_token = get_access_token()
#         if not access_token:
#             raise ValueError("Failed to obtain access token")
#
#         # Generate timestamp and password
#         timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
#         password = generate_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)
#
#         payload = {
#             "BusinessShortCode": settings.MPESA_SHORTCODE,
#             "Password": password,
#             "Timestamp": timestamp,
#             "TransactionType": "CustomerPayBillOnline",
#             "Amount": amount,
#             "PartyA": "0714441708",
#             "PartyB": settings.MPESA_SHORTCODE,
#             "PhoneNumber": "0714441708",
#             "CallBackURL": "https://comm-commission-quit-couple.trycloudflare.com/mpesa/callback/",
#             "AccountReference": account_reference,
#             "TransactionDesc": transaction_desc
#         }
#
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#
#         # Make the API request
#         stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
#         response = requests.post(stk_url, json=payload, headers=headers, timeout=30)
#         response.raise_for_status()
#
#         return response.json()
#
#     except requests.exceptions.RequestException as e:
#         logger.error(f"M-Pesa API request failed: {str(e)}")
#         if hasattr(e, 'response') and e.response:
#             logger.error(f"Response status: {e.response.status_code}")
#             logger.error(f"Response content: {e.response.text}")
#         raise ValueError("Failed to initiate payment. Please try again later.")
#     except Exception as e:
#         logger.error(f"Error in lipa_na_mpesa: {str(e)}")
#         raise
#
#     # In your lipa_na_mpesa() function, print the payload before sending:
#     print("STK Push Payload:", json.dumps(payload, indent=2))
#     print("Headers:", headers)