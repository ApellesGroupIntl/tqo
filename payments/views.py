import base64
from datetime import time
from random import random

from django.contrib.sites import requests
from rest_framework.utils import timezone
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from .forms import PhoneForm
from django.contrib import messages
import random
from rest_framework import status
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.db import transaction
import json
import logging
from .models import Payment
from .utils import generate_ticket_pdf
from events.models import Event
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Payment
from .mpesa import get_access_token, lipa_na_mpesa
from django.conf import settings
import base64
import requests
import json
logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
def initiate_stk_push(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
        phone = data.get("phone_number")
        amount = data.get("amount")
        event_name = data.get("event_name")

        if not all([phone, amount, event_name]):
            return JsonResponse({"success": False, "message": "Missing required fields"}, status=400)

        # Normalize phone
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("+"):
            phone = phone[1:]

        # Find event by name (case-insensitive)
        event = Event.objects.filter(title__iexact=event_name).first()
        if not event:
            return JsonResponse({"success": False, "message": "Event not found"}, status=404)

        # Save pending payment
        payment = Payment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            event=event,
            phone_number=phone,
            amount=amount,
            amount_integer=int(float(amount)),
            status="pending"
        )

        # Initiate STK Push
        callback_url = f"{request.scheme}://{request.get_host()}/payments/mpesa-callback/"
        response = lipa_na_mpesa(
            phone_number=phone,
            amount=amount,
            account_reference=f"{event.title} - Payment-{payment.id}",
            transaction_desc=f"{event.title} Ticket Payment",
            callback_url=callback_url
        )

        # Save CheckoutRequestID
        checkout_request_id = response.get("CheckoutRequestID")
        payment.checkout_request_id = checkout_request_id
        payment.save()

        return JsonResponse({
            "success": True,
            "checkout_request_id": checkout_request_id,
            "message": "STK Push sent. Enter your M-Pesa PIN."
        })

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)



@csrf_exempt
def stk_callback(request):
    """
    This endpoint receives the STK Push result from Safaricom.
    It updates the Payment object with status and transaction details.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        print("STK Callback received:", data)  # For debugging

        result = data.get("Body", {}).get("stkCallback", {})
        checkout_request_id = result.get("CheckoutRequestID")
        result_code = result.get("ResultCode")
        result_desc = result.get("ResultDesc")

        # Find the payment record
        payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
        if not payment:
            return JsonResponse({"success": False, "message": "Payment not found"}, status=404)

        if result_code == 0:
            # Payment successful
            payment.status = "success"
            # Optional: store transaction details
            callback_metadata = result.get("CallbackMetadata", {}).get("Item", [])
            mpesa_receipt = next((i["Value"] for i in callback_metadata if i["Name"] == "MpesaReceiptNumber"), None)
            payment.transaction_id = mpesa_receipt
            payment.save()
        else:
            # Payment failed
            payment.status = "failed"
            payment.message = result_desc
            payment.save()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class STKPushView(APIView):
    permission_classes = [AllowAny]   # ✅ Safaricom must be able to reach this

    def post(self, request):
        try:
            data = json.loads(request.body)
            logger.debug(f"STK Callback received: {data}")

            checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']
            result_code = data['Body']['stkCallback']['ResultCode']

            payment = Payment.objects.get(checkout_request_id=checkout_request_id)

            if result_code == 0:
                metadata = data['Body']['stkCallback']['CallbackMetadata']['Item']
                receipt_number = next(item['Value'] for item in metadata if item['Name'] == 'MpesaReceiptNumber')

                payment.status = "success"
                payment.mpesa_receipt_number = receipt_number
            else:
                payment.status = "failed"

            payment.save()
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Processed successfully"})

        except Exception as e:
            logger.error(f"STK callback error: {str(e)}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": f"Error: {str(e)}"})



class CheckPaymentStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, checkout_request_id):
        payment = get_object_or_404(Payment, checkout_request_id=checkout_request_id)
        return Response({
            "status": payment.status,
            "checkout_request_id": payment.checkout_request_id,
            "mpesa_receipt_number": payment.mpesa_receipt_number,
            "amount": payment.amount,
            "status_message": payment.status_message
        })

@csrf_exempt
def mpesa_callback(request):
    """
    M-Pesa STK Push callback endpoint.
    Updates Payment status in the database.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
        body = data.get("Body", {})
        stk_callback = body.get("stkCallback", {})

        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

        payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
        if not payment:
            logger.warning(f"Payment not found for CheckoutRequestID: {checkout_request_id}")
            return JsonResponse({"error": "Payment not found"}, status=404)

        if result_code == 0:
            # Payment successful
            mpesa_receipt_number = None
            amount = None
            for item in callback_metadata:
                if item.get("Name") == "MpesaReceiptNumber":
                    mpesa_receipt_number = item.get("Value")
                if item.get("Name") == "Amount":
                    amount = item.get("Value")

            payment.status = "success"
            payment.mpesa_receipt_number = mpesa_receipt_number
            payment.amount_integer = int(amount) if amount else payment.amount_integer
            payment.status_message = result_desc
        else:
            # Payment failed
            payment.status = "failed"
            payment.status_message = result_desc

        payment.save()

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback received successfully"})

    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = json.loads(request.body)
            callback_data = data.get("Body", {}).get("stkCallback", {})
            result_code = callback_data.get("ResultCode")
            checkout_request_id = callback_data.get("CheckoutRequestID")

            if not checkout_request_id:
                logger.error("Missing checkout_request_id in callback")
                return Response({"status": "error", "message": "Missing checkout ID"}, status=400)

            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(
                    checkout_request_id=checkout_request_id
                )

                if result_code == 0:  # Success
                    self._handle_successful_payment(payment, callback_data)
                    logger.info(f"Payment {checkout_request_id} processed successfully")
                else:  # Failure
                    self._handle_failed_payment(payment, callback_data)
                    logger.warning(f"Payment {checkout_request_id} failed")

            return Response({"status": "success"}, status=200)

        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {checkout_request_id}")
            return Response({"status": "error", "message": "Payment not found"}, status=404)
        except Exception as e:
            logger.exception("Unexpected error processing callback")
            return Response({"status": "error", "message": str(e)}, status=500)

    def _handle_successful_payment(self, payment, callback_data):
        metadata_items = callback_data.get("CallbackMetadata", {}).get("Item", [])
        metadata = {item["Name"]: item["Value"]
                    for item in metadata_items
                    if "Name" in item and "Value" in item}

        payment.status = 'success'
        payment.mpesa_receipt_number = metadata.get("MpesaReceiptNumber", "")[:50]
        payment.amount = Decimal(str(metadata.get("Amount", payment.amount)))
        payment.phone_number = metadata.get("PhoneNumber", payment.phone_number)[:15]
        payment.save()

        # Generate ticket asynchronously
        transaction.on_commit(lambda: generate_ticket_async(payment.id))

    def _handle_failed_payment(self, payment, callback_data):
        payment.status = 'failed'
        payment.status_message = callback_data.get("ResultDesc", "Payment failed")[:255]
        payment.save()


def generate_ticket_async(payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        ticket_file = generate_ticket_pdf(payment)

        # Save the generated ticket to the payment
        payment.ticket.save(
            f'ticket_{payment.id}.pdf',
            ContentFile(ticket_file.getvalue()),
            save=True
        )
        logger.info(f"Ticket generated for payment {payment.id}")
    except Exception as e:
        logger.error(f"Error generating ticket: {str(e)}")
        # Implement retry logic here if needed

@method_decorator(login_required(login_url="/login"), name='dispatch')
class PaymentStatusView(APIView):
    # permission_classes = [IsAuthenticated]
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        checkout_request_id = request.query_params.get('checkout_request_id')
        if not checkout_request_id:
            return Response(
                {'success': False, 'message': 'checkout_request_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(
                checkout_request_id=checkout_request_id,
                user=request.user
            )

            # If still pending after 5 minutes, consider checking with M-Pesa directly
            if payment.status == 'pending' and (timezone.now() - payment.created_at).seconds > 300:
                self._check_mpesa_status(payment)
                payment.refresh_from_db()

            return Response({
                'success': True,
                'status': payment.status,
                'transaction_id': payment.mpesa_receipt_number,
                'message': payment.status_message or ''
            })

        except Payment.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return Response(
                {'success': False, 'message': 'Error checking payment status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _check_mpesa_status(self, payment):
        """Optional: Implement direct status check with M-Pesa API"""
        try:
            # This would call M-Pesa's transaction status API
            # Implement based on your M-Pesa integration
            pass
        except Exception as e:
            logger.error(f"Error checking M-Pesa status: {str(e)}")

def payment_success(request, transaction_id):
    payment = get_object_or_404(Payment, mpesa_receipt=transaction_id, user=request.user)
    return render(request, 'payments/success.html', {
        'payment': payment,
        'event': payment.event
    })

@ensure_csrf_cookie
@login_required
def checkout(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        ticket_type_id = request.POST.get("ticket_type")
        quantity = int(request.POST.get("quantity", 1))
        phone = request.POST.get("phone")
        email = request.POST.get("email")

        ticket_type = get_object_or_404(event.ticket_types.all(), pk=ticket_type_id)
        total_price = ticket_type.price * quantity

        return render(request, "payments/checkout.html", {
            "event": event,
            "ticket": ticket_type,
            "quantity": quantity,
            "total_price": total_price,
            "phone": phone,
            "email": email,
        })

    # If GET, redirect back to selection page
    return redirect("ticket_selection", event_id=event_id)


def mpesa_payment(request, event_id, amount_integer=None):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        # Get form data
        phone = request.POST.get('phone')
        ticket_type_id = request.POST.get('ticket_type')
        quantity = int(request.POST.get('quantity', 1))

        try:
            # Normalize phone number
            phone = normalize_phone(phone)

            # Calculate amount (replace with your actual calculation)
            amount = event.price * quantity

            # Generate unique transaction reference
            transaction_ref = f"TQO{event_id}{random.randint(1000, 9999)}"

            # Get callback URL
            callback_url = request.build_absolute_uri(
                reverse('payments:mpesa_callback')
            )

            # Initiate STK Push
            response = lipa_na_mpesa(
                phone_number=phone,
                amount=amount,
                account_reference=transaction_ref,
                transaction_desc=f"Payment for {event.title}",
                callback_url=callback_url
            )

            # Check if STK Push was initiated successfully
            if response.get('ResponseCode') == '0':
                # Create pending payment record
                payment = Payment.objects.create(
                    user=request.user,
                    event=event,
                    amount=amount,
                    amount_integer=amount_integer,  # Add this line
                    phone=phone,
                    checkout_request_id=response.get('CheckoutRequestID'),
                    status_message=response.get("ResponseDescription", ""),
                status='pending'
                )

                # Redirect to confirmation page
                return render(request, 'payments/payment_pending.html', {
                    'event': event,
                    'payment': payment,
                    'checkout_request_id': response.get('CheckoutRequestID')
                })
            else:
                messages.error(request, "Failed to initiate payment. Please try again.")
                return redirect('payments:checkout', event_id=event_id)

        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('payments:checkout', event_id=event_id)

    # If GET request, show payment form
    return redirect('payments:checkout', event_id=event_id)

@login_required
def payment_status(request):
    """
    Returns the current status of a payment given a checkout_request_id.
    """
    checkout_request_id = request.GET.get("checkout_request_id")
    if not checkout_request_id:
        return JsonResponse(
            {"status": "error", "message": "checkout_request_id is required"},
            status=400
        )

    payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
    if not payment:
        return JsonResponse(
            {"status": "error", "message": "Payment not found"},
            status=404
        )

    # Normalize backend status to frontend expected status
    status_map = {
        "success": "success",
        "failed": "failed",
        "pending": "pending",
    }
    status = status_map.get(payment.status.lower(), "pending")

    response = {
        "status": status,
        "transaction_id": payment.mpesa_receipt_number or "",
        "amount": payment.amount_integer or 0,
        "message": getattr(payment, "status_message", f"Payment is {status}"),
        "event": payment.event.title if payment.event else "",
    }

    return JsonResponse(response)
def my_tickets(request):
    tickets = Payment.objects.filter(user=request.user, status='success')
    return render(request, 'payments/my_tickets.html', {'tickets': tickets})

def normalize_phone(phone):
    phone = str(phone).strip().replace("+", "")
    if phone.startswith("0"):
        return "254" + phone[1:]
    elif phone.startswith("7"):
        return "254" + phone
    return phone

@login_required
def buy_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = PhoneForm(request.POST)
        if form.is_valid():
            phone = normalize_phone(form.cleaned_data['phone'])

            # Create Payment object
            payment = Payment.objects.create(
                user=request.user,
                event=event,
                phone_number=phone,
                amount=event.price,
                status='pending'
            )

            # Call STK Push
            callback_url = request.build_absolute_uri(reverse('payments:mpesa_callback'))

            lipa_na_mpesa(
                phone_number=phone,
                amount=event.price,
                account_reference=str(event.id),
                transaction_desc=f"Payment for {event.title}",
                callback_url=callback_url
            )

            return render(request, 'payments/confirm_payment.html', {
                'event': event,
                'payment': payment,
                'message': "STK Push sent. Check your phone."
            })
    else:
        form = PhoneForm()

    return render(request, 'payments/buy_ticket.html', {'event': event, 'form': form})


# ✅ Ticket Download View
class DownloadTicketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, user=request.user, status='success')
            if not payment.ticket:
                raise Http404
            return FileResponse(payment.ticket.open(), as_attachment=True, filename=payment.ticket.name)
        except Payment.DoesNotExist:
            raise Http404


# ✅ Ticket Preview View
@login_required
def preview_ticket(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user, status='success')
        if not payment.ticket:
            raise Http404
        return FileResponse(payment.ticket.open(), content_type='application/pdf')
    except Payment.DoesNotExist:
        raise Http404


logger.debug(f"Authorization Header: Bearer {get_access_token()}")


@login_required
def download_ticket(request, payment_id):
    """
    View to download a ticket PDF for a completed payment
    """
    try:
        payment = Payment.objects.get(
            id=payment_id,
            user=request.user,
            status='success'
        )

        if not payment.ticket:
            raise Http404("Ticket not generated yet")

        response = FileResponse(
            payment.ticket.open(),
            as_attachment=True,
            filename=f"ticket_{payment.id}.pdf"
        )
        return response

    except Payment.DoesNotExist:
        raise Http404("Ticket not found")
