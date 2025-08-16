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

# def get_access_token():
#     consumer_key = settings.MPESA_CONSUMER_KEY
#     consumer_secret = settings.MPESA_CONSUMER_SECRET
#     logger.debug(f"Consumer Key: {consumer_key[:4]}... (length {len(consumer_key)})")
#     logger.debug(f"Consumer Secret: {consumer_secret[:4]}... (length {len(consumer_secret)})")
#
#     raw_credentials = f"{consumer_key}:{consumer_secret}"
#     encoded_credentials = base64.b64encode(raw_credentials.encode()).decode()
#     logger.debug(f"Authorization Header: Basic {encoded_credentials}")
#
#     auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
#     response = requests.get(
#         auth_url,
#         headers={
#             'Authorization': f'Basic {encoded_credentials}',
#             'Content-Type': 'application/json'
#         }
#     )
#
#     logger.debug(f"Auth Response: {response.status_code} - {response.text}")
#     response.raise_for_status()
#     return response.json()['access_token']


def get_access_token():
    """Get OAuth access token from M-Pesa API with better error handling"""
    try:
        auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

        response = requests.get(
            auth_url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            headers={'Content-Type': 'application/json'},
            timeout=30  # ✅ FIXED: reasonable timeout (30 seconds)
        )

        # Debug response logging
        logger.debug(f"Auth response: {response.status_code} - {response.text}")

        response.raise_for_status()
        data = response.json()

        if 'access_token' not in data:
            logger.error("No access_token in response")
            raise ValueError("Invalid token response")

        token = data['access_token']
        logger.info("Successfully retrieved M-Pesa access token")
        return token

    except requests.exceptions.Timeout:
        logger.error("Request timed out while fetching M-Pesa access token")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error while fetching access token: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


# def get_access_token():
#     """
#     Get M-Pesa OAuth token only when called.
#     """
#     consumer_key = settings.MPESA_CONSUMER_KEY
#     consumer_secret = settings.MPESA_CONSUMER_SECRET
#     auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
#
#     logger.debug("Fetching M-Pesa access token...")
#
#     credentials = f"{consumer_key}:{consumer_secret}"
#     encoded_credentials = base64.b64encode(credentials.encode()).decode()
#
#     headers = {
#         "Authorization": f"Basic {encoded_credentials}"
#     }
#
#     response = requests.get(auth_url, headers=headers)
#     try:
#         response.raise_for_status()
#         token = response.json().get("access_token")
#         logger.debug(f"M-Pesa Access Token fetched successfully: {token}")
#         return token
#     except requests.exceptions.HTTPError as e:
#         logger.error(f"Failed to fetch M-Pesa access token: {e} - Response: {response.text}")
#         raise


def lipa_na_mpesa(phone_number, amount, account_reference, transaction_desc, callback_url):
    """Initiate STK push payment request with dynamic inputs"""
    try:
        if not all([phone_number, amount, account_reference, transaction_desc, callback_url]):
            raise ValueError("All parameters are required")

        amount = int(float(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # access_token = get_access_token()
        access_token = get_access_token()  # ✅ Token fetched here, only when called
        logger.debug(f"Using token for Lipa na M-Pesa: {access_token}")
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = generate_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,  # use actual user phone
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,# use actual user phone
            # "phoneNumber": phone_number,
            "CallBackURL": "https://escape-backing-savings-army.trycloudflare.com/payments/mpesa-callback/",
            # "CallBackURL": "https://ram-letting-lounge-designated.trycloudflare.com/payments/initiate-stk-push/",
            # "CallBackURL": callback_url,
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




