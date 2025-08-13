from random import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.urls import reverse
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe

from .models import Payment
from .forms import PhoneForm
from .mpesa import lipa_na_mpesa, access_token
from .utils import generate_ticket_pdf
from events.models import Event
from django.contrib import messages
# payments/views.py
from django.conf import settings
from django.urls import reverse
from .mpesa import lipa_na_mpesa
import random

# payments/views.py
from django.http import JsonResponse


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import json
from .models import Payment
from .utils import generate_ticket_pdf

logger = logging.getLogger(__name__)
# payments/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
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
from .mpesa import lipa_na_mpesa
from .utils import generate_ticket_pdf
from events.models import Event

logger = logging.getLogger(__name__)



# class InitiateSTKPushView(APIView):
#     authentication_classes = [SessionAuthentication]  # Add this
#     permission_classes = (AllowAny, IsAuthenticated)
#     # permission_classes = (AllowAny,)
#
#     @method_decorator(csrf_exempt)
#     def dispatch(self, *args, **kwargs):
#         return super().dispatch(*args, **kwargs)
#
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             phone = data.get('phone', '').strip()
#             amount = data.get('amount')
#             event_id = data.get('event_id')
#
#             # Validate inputs
#             if not all([phone, amount, event_id]):
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Missing required fields'
#                 }, status=400)
#
#             # Validate phone number
#             if not (phone.startswith('2547') and len(phone) == 12):
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Invalid phone number format. Use Safaricom format (2547XXXXXXXX)'
#                 }, status=400)
#
#             # Get event
#             event = get_object_or_404(Event, id=event_id)
#
#             # Generate callback URL
#             callback_url = request.build_absolute_uri(
#                 reverse('payments:mpesa_callback')
#             )
#
#             # Generate unique reference
#             transaction_ref = f"TQO{event_id}{request.user.id}"
#
#             with transaction.atomic():
#                 # Create payment record first
#                 payment = Payment.objects.create(
#                     user=request.user,
#                     event=event,
#                     amount=amount,
#                     phone=phone,
#                     status='pending'
#                 )
#
#                 # Initiate STK Push
#                 response = lipa_na_mpesa(
#                     phone_number=phone,
#                     amount=amount,
#                     account_reference=transaction_ref,
#                     transaction_desc=f"Payment for {event.title}",
#                     callback_url=callback_url
#                 )
#
#                 if response.get('ResponseCode') == '0':
#                     # Update payment with checkout request ID
#                     payment.transaction_id = response['CheckoutRequestID']
#                     payment.save()
#
#                     return JsonResponse({
#                         'success': True,
#                         'checkout_request_id': response['CheckoutRequestID'],
#                         'message': 'Payment request sent to your phone'
#                     })
#                 else:
#                     # Update payment status if STK push failed
#                     payment.status = 'failed'
#                     payment.status_message = response.get('errorMessage', 'STK push failed')
#                     payment.save()
#
#                     return JsonResponse({
#                         'success': False,
#                         'message': response.get('errorMessage', 'Failed to initiate payment')
#                     }, status=400)
#
#         except Exception as e:
#             logger.error(f"Error initiating STK push: {str(e)}")
#             return JsonResponse({
#                 'success': False,
#                 'message': 'An error occurred while processing your payment'
#             }, status=500)

# payments/views.py
@method_decorator(csrf_exempt, name='dispatch')
class InitiateSTKPushView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    # authentication_classes = []
    # permission_classes = []

    def post(self, request):
        try:
            # Read the request body once and store it
            body = request.body.decode('utf-8')
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)

            phone = data.get('phone', '').strip()
            amount = data.get('amount')
            event_id = data.get('event_id')

            # Validate inputs
            if not all([phone, amount, event_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields'
                }, status=400)

            # Validate phone number
            if not (phone.startswith('2547') and len(phone) == 12):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid phone number format. Use Safaricom format (2547XXXXXXXX)'
                }, status=400)

            # Get event
            event = get_object_or_404(Event, id=event_id)

            # Generate callback URL
            callback_url = request.build_absolute_uri(
                reverse('payments:mpesa_callback')
            )

            # Generate unique reference
            transaction_ref = f"TQO{event_id}{request.user.id}"

            with transaction.atomic():
                # Create payment record first
                payment = Payment.objects.create(
                    user=request.user,
                    event=event,
                    amount=amount,
                    phone=phone,
                    status='pending'
                )

                # Initiate STK Push
                response = lipa_na_mpesa(
                    phone_number=phone,
                    amount=amount,
                    account_reference=transaction_ref,
                    transaction_desc=f"Payment for {event.title}",
                    callback_url=callback_url
                )

                if response.get('ResponseCode') == '0':
                    # Update payment with checkout request ID
                    payment.transaction_id = response['CheckoutRequestID']
                    payment.save()

                    return JsonResponse({
                        'success': True,
                        'checkout_request_id': response['CheckoutRequestID'],
                        'message': 'Payment request sent to your phone'
                    })
                else:
                    # Update payment status if STK push failed
                    payment.status = 'failed'
                    payment.status_message = response.get('errorMessage', 'STK push failed')
                    payment.save()

                    return JsonResponse({
                        'success': False,
                        'message': response.get('errorMessage', 'Failed to initiate payment')
                    }, status=400)

        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while processing your payment'
            }, status=500)

class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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
                    transaction_id=checkout_request_id
                )

                if result_code == "0":
                    # Successful payment
                    self._handle_successful_payment(payment, callback_data)
                    logger.info(f"Payment {checkout_request_id} processed successfully")
                else:
                    # Failed payment
                    self._handle_failed_payment(payment, callback_data.get("ResultDesc"))
                    logger.warning(f"Payment {checkout_request_id} failed")

            return Response({"status": "success"}, status=200)

        except Payment.DoesNotExist:
            logger.error(f"Payment not found for checkout_request_id: {checkout_request_id}")
            return Response({"status": "error", "message": "Payment not found"}, status=404)
        except Exception as e:
            logger.exception("Unexpected error processing M-Pesa callback")
            return Response({"status": "error", "message": str(e)}, status=500)

    def _handle_successful_payment(self, payment, callback_data):
        """Process a successful payment callback"""
        payment.status = 'success'

        # Extract metadata from callback
        metadata = callback_data.get("CallbackMetadata", {}).get("Item", [])
        metadata_map = {item.get("Name"): item.get("Value") for item in metadata}

        # Update payment details
        payment.mpesa_receipt = metadata_map.get("MpesaReceiptNumber")
        payment.amount = float(metadata_map.get("Amount", payment.amount))
        payment.phone = metadata_map.get("PhoneNumber", payment.phone)
        payment.save()

        # Generate ticket
        try:
            generate_ticket_pdf(payment)
        except Exception as e:
            logger.error(f"Error generating ticket for payment {payment.id}: {str(e)}")

    def _handle_failed_payment(self, payment, failure_reason):
        """Process a failed payment callback"""
        payment.status = 'failed'
        payment.status_message = failure_reason[:255]  # Truncate if too long
        payment.save()

class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        checkout_request_id = request.GET.get('checkout_request_id')
        if not checkout_request_id:
            return JsonResponse({'status': 'error', 'message': 'Missing checkout ID'}, status=400)

        payment = get_object_or_404(Payment, transaction_id=checkout_request_id, user=request.user)
        return JsonResponse({
            'status': payment.status,
            'transaction_id': payment.mpesa_receipt if payment.status == 'success' else None,
            'message': payment.status_message if payment.status == 'failed' else None
        })

def payment_success(request, transaction_id):
    payment = get_object_or_404(Payment, mpesa_receipt=transaction_id, user=request.user)
    return render(request, 'payments/success.html', {
        'payment': payment,
        'event': payment.event
    })

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



# def checkout(request, event_id):
#     event = get_object_or_404(Event, id=event_id)
#
#     # Get quantity from query params or form, default to 1
#     quantity = int(request.GET.get('quantity', 1))
#
#     # If your Event model has multiple ticket types, fetch the one selected earlier
#     # Otherwise, assume event.price is the ticket price
#     ticket = {
#         'ticket_type': 'Standard Ticket',  # Change this if you have a Ticket model
#         'price': event.price
#     }
#
#     total_price = event.price * quantity
#
#     context = {
#         'event': event,
#         'ticket': ticket,
#         'quantity': quantity,
#         'total_price': total_price
#     }
#     return render(request, 'payments/checkout.html', context)


# class PaymentStatusView(APIView):
#     def get(self, request):
#         checkout_request_id = request.GET.get('checkout_request_id')
#         if not checkout_request_id:
#             return JsonResponse({'status': 'error', 'message': 'Missing checkout ID'}, status=400)
#
#         payment = get_object_or_404(Payment, checkout_request_id=checkout_request_id)
#         return JsonResponse({
#             'status': payment.status,
#             'transaction_id': payment.mpesa_code if payment.status == 'success' else None
#         })

# payments/views.py

# @method_decorator(csrf_exempt, name='dispatch')
# class InitiateSTKPushView(APIView):
#     def post(self, request):
#         try:
#             # Parse and validate request data
#             try:
#                 data = json.loads(request.body)
#                 phone = data.get('phone', '').strip()
#                 amount = float(data.get('amount', 0))
#                 event_id = data.get('event_id')
#
#                 # Validate phone number format
#                 if not phone.startswith('2547') or len(phone) != 12:
#                     return JsonResponse({
#                         'success': False,
#                         'message': 'Invalid phone number. Use Safaricom format (2547XXXXXXXX)'
#                     }, status=400)
#
#                 # Validate amount
#                 if amount <= 0:
#                     return JsonResponse({
#                         'success': False,
#                         'message': 'Amount must be greater than 0'
#                     }, status=400)
#
#             except (ValueError, KeyError, json.JSONDecodeError) as e:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Invalid request data'
#                 }, status=400)
#
#             # Get the event
#             try:
#                 event = Event.objects.get(id=event_id)
#             except Event.DoesNotExist:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Event not found'
#                 }, status=404)
#
#             # Process payment
#             callback_url = request.build_absolute_uri(
#                 reverse('payments:mpesa_callback')
#             )
#
#             # Generate unique reference
#             transaction_ref = f"TQO{event_id}{random.randint(1000, 9999)}"
#
#             response = lipa_na_mpesa(
#                 phone_number=phone,
#                 amount=amount,
#                 account_reference=transaction_ref,
#                 transaction_desc=f"Payment for Event {event.title}",
#                 callback_url=callback_url
#             )
#
#             if response.get('ResponseCode') == '0':
#                 # Create payment record
#                 payment = Payment.objects.create(
#                     user=request.user,
#                     event=event,
#                     amount=amount,
#                     phone=phone,
#                     transaction_id=response['CheckoutRequestID'],
#                     status='pending'
#                 )
#
#                 return JsonResponse({
#                     'success': True,
#                     'checkout_request_id': response['CheckoutRequestID'],
#                     'message': 'STK Push initiated successfully'
#                 })
#
#             return JsonResponse({
#                 'success': False,
#                 'message': response.get('errorMessage', 'Failed to initiate payment')
#             }, status=400)
#
#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'message': f'Server error: {str(e)}'
#             }, status=500)
# def initiate_stk_push(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             phone = data.get('phone')
#             amount = data.get('amount')
#             event_id = data.get('event_id')
#
#             # Normalize phone number
#             phone = normalize_phone(phone)
#
#             # Generate unique reference
#             transaction_ref = f"TQO{event_id}{random.randint(1000, 9999)}"
#
#             # Initiate STK Push
#             callback_url = request.build_absolute_uri(reverse('payments:mpesa_callback'))
#             response = lipa_na_mpesa(
#                 phone_number=phone,
#                 amount=amount,
#                 account_reference=transaction_ref,
#                 transaction_desc=f"Payment for Event {event_id}",
#                 callback_url=callback_url
#             )
#
#             if response.get('ResponseCode') == '0':
#                 # Create payment record
#                 payment = Payment.objects.create(
#                     user=request.user,
#                     event_id=event_id,
#                     amount=amount,
#                     phone=phone,
#                     transaction_id=response.get('CheckoutRequestID'),
#                     status='pending'
#                 )
#
#                 return JsonResponse({
#                     'success': True,
#                     'checkout_request_id': response.get('CheckoutRequestID')
#                 })
#
#             return JsonResponse({
#                 'success': False,
#                 'message': response.get('errorMessage', 'Failed to initiate payment')
#             })
#
#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'message': str(e)
#             }, status=400)
#
#     return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def mpesa_payment(request, event_id):
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
                    phone=phone,
                    transaction_id=response.get('CheckoutRequestID'),
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


def check_payment_status(request):
    checkout_request_id = request.GET.get('checkout_request_id')
    payment = get_object_or_404(Payment, transaction_id=checkout_request_id)

    return JsonResponse({
        'status': payment.status,
        'transaction_id': payment.transaction_id
    })

# def mpesa_payment(request, event_id):
#     event = get_object_or_404(Event, id=event_id)
#
#     if request.method == 'POST':
#         # Get form data
#         phone = request.POST.get('phone')
#         ticket_type_id = request.POST.get('ticket_type')
#         quantity = int(request.POST.get('quantity', 1))
#
#         try:
#             # Process M-Pesa payment (replace with your actual payment logic)
#             # This is where you would integrate with the M-Pesa API
#             transaction_id = "MPESA" + str(random.randint(100000, 999999))
#             amount = 1000  # Replace with actual amount calculation
#
#             # Create payment record (simplified example)
#             payment = Payment.objects.create(
#                 user=request.user,
#                 event=event,
#                 amount=amount,
#                 phone=phone,
#                 transaction_id=transaction_id,
#                 status='success'
#             )
#
#             # Redirect to success page
#             return render(request, 'payments/success.html', {
#                 'event': event,
#                 'amount': amount,
#                 'transaction_id': transaction_id
#             })
#
#         except Exception as e:
#             messages.error(request, f"Payment failed: {str(e)}")
#             return render(request, 'payments/payment.html', {'event': event})
#
#     # If GET request, show payment form
#     return render(request, 'payments/payment.html', {'event': event})
#

# def mpesa_payment(request, event_id, payment_successful, amount=None, transaction_id=None):
#     event = get_object_or_404(Event, id=event_id)
#
#     if payment_successful:  # Your success condition
#         return render(request, 'payments/success.html', {
#             'event': event,
#             'amount': amount,
#             'transaction_id': transaction_id
#         })
#
#     if request.method == 'POST':
#         phone = request.POST.get('phone')
#         # TODO: Trigger M-Pesa STK push here
#         return render(request, 'payments/success.html', {'event': event})
#
#     return render(request, 'payments/checkout.html', {'event': event})

@login_required
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


# class MpesaCallbackView(APIView):
#     """
#     Handle M-Pesa STK Push callback notifications.
#     This endpoint receives payment confirmation from M-Pesa and updates the payment status accordingly.
#     """
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         try:
#             # Parse and validate incoming data
#             try:
#                 data = json.loads(request.body)
#                 callback_data = data.get("Body", {}).get("stkCallback", {})
#                 if not callback_data:
#                     raise ValueError("Invalid callback data structure")
#             except (json.JSONDecodeError, ValueError) as e:
#                 logger.error(f"Invalid callback data: {str(e)}")
#                 return Response({"status": "error", "message": "Invalid callback data"}, status=400)
#
#             # Extract essential fields
#             result_code = callback_data.get("ResultCode")
#             checkout_request_id = callback_data.get("CheckoutRequestID")
#             result_desc = callback_data.get("ResultDesc", "No description provided")
#
#             if not checkout_request_id:
#                 logger.error("Missing checkout_request_id in callback")
#                 return Response({"status": "error", "message": "Missing checkout ID"}, status=400)
#
#             try:
#                 # Use atomic transaction to ensure data consistency
#                 with transaction.atomic():
#                     payment = Payment.objects.select_for_update().get(transaction_id=checkout_request_id)
#
#                     if result_code == "0":
#                         # Successful payment
#                         self._handle_successful_payment(payment, callback_data)
#                         logger.info(f"Payment {checkout_request_id} processed successfully")
#                     else:
#                         # Failed payment
#                         self._handle_failed_payment(payment, result_desc)
#                         logger.warning(f"Payment {checkout_request_id} failed: {result_desc}")
#
#             except Payment.DoesNotExist:
#                 logger.error(f"Payment not found for checkout_request_id: {checkout_request_id}")
#                 return Response({"status": "error", "message": "Payment not found"}, status=404)
#             except Exception as e:
#                 logger.error(f"Error processing payment {checkout_request_id}: {str(e)}")
#                 raise  # Will be caught by the outer try-except
#
#             return Response({"status": "success"}, status=200)
#
#         except Exception as e:
#             logger.exception("Unexpected error processing M-Pesa callback")
#             return Response({"status": "error", "message": str(e)}, status=500)
#
#     def _handle_successful_payment(self, payment, callback_data):
#         """Process a successful payment callback"""
#         payment.status = 'success'
#
#         # Extract metadata from callback
#         metadata = callback_data.get("CallbackMetadata", {}).get("Item", [])
#         metadata_map = {item.get("Name"): item.get("Value") for item in metadata}
#
#         # Update payment details
#         payment.mpesa_receipt = metadata_map.get("MpesaReceiptNumber")
#         payment.amount = float(metadata_map.get("Amount", payment.amount))
#         payment.phone = metadata_map.get("PhoneNumber", payment.phone)
#
#         payment.save()
#
#         # Generate ticket (in a separate try-except to avoid failing the whole transaction)
#         try:
#             generate_ticket_pdf(payment)
#         except Exception as e:
#             logger.error(f"Error generating ticket for payment {payment.id}: {str(e)}")
#
#     def _handle_failed_payment(self, payment, failure_reason):
#         """Process a failed payment callback"""
#         payment.status = 'failed'
#         payment.status_message = failure_reason[:255]  # Ensure it fits in the field
#         payment.save()

# payments/views.py
logger.debug(f"Authorization Header: Bearer {access_token}")

@method_decorator(csrf_exempt, name='dispatch')
# class MpesaCallbackView(APIView):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             callback_data = data.get("Body", {}).get("stkCallback", {})
#             result_code = callback_data.get("ResultCode")
#             checkout_request_id = callback_data.get("CheckoutRequestID")
#
#             if not checkout_request_id:
#                 return Response({"status": "error", "message": "Missing checkout ID"}, status=400)
#
#             try:
#                 payment = Payment.objects.get(transaction_id=checkout_request_id)
#             except Payment.DoesNotExist:
#                 return Response({"status": "error", "message": "Payment not found"}, status=404)
#
#             if result_code == "0":
#                 # Successful payment
#                 payment.status = 'success'
#
#                 # Extract M-Pesa details from callback
#                 callback_metadata = callback_data.get("CallbackMetadata", {}).get("Item", [])
#                 for item in callback_metadata:
#                     if item.get("Name") == "MpesaReceiptNumber":
#                         payment.mpesa_receipt = item.get("Value")
#                     elif item.get("Name") == "Amount":
#                         payment.amount = float(item.get("Value"))
#                     elif item.get("Name") == "PhoneNumber":
#                         payment.phone = item.get("Value")
#
#                 payment.save()
#
#                 # Generate ticket PDF
#                 generate_ticket_pdf(payment)
#
#             else:
#                 payment.status = 'failed'
#                 payment.status_message = callback_data.get("ResultDesc", "Payment failed")
#                 payment.save()
#
#             return Response({"status": "success"}, status=200)
#
#         except Exception as e:
#             return Response({"status": "error", "message": str(e)}, status=400)

# class MpesaCallbackView(APIView):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             stk_callback = data.get("Body", {}).get("stkCallback", {})
#             result_code = stk_callback.get("ResultCode")
#             checkout_request_id = stk_callback.get("CheckoutRequestID")
#
#             payment = Payment.objects.filter(transaction_id=checkout_request_id).first()
#
#             if payment:
#                 if result_code == "0":
#                     # Successful payment
#                     payment.status = 'success'
#
#                     # Get M-Pesa receipt number from callback metadata
#                     metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
#                     for item in metadata:
#                         if item.get("Name") == "MpesaReceiptNumber":
#                             payment.mpesa_receipt = item.get("Value")
#                             break
#
#                     payment.save()
#
#                     # Generate ticket (implement your ticket generation logic)
#                     # generate_ticket_pdf(payment)
#
#                 else:
#                     payment.status = 'failed'
#                     payment.save()
#
#             return Response({"status": "success"}, status=200)
#
#         except Exception as e:
#             return Response({"error": str(e)}, status=400)

# # ✅ M-Pesa Callback View
# @method_decorator(csrf_exempt, name='dispatch')
# class MpesaCallbackView(APIView):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             stk_callback = data["Body"]["stkCallback"]
#             result_code = stk_callback["ResultCode"]
#             metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
#
#             receipt = None
#             phone = None
#             amount = None
#
#             for item in metadata:
#                 name = item.get("Name")
#                 value = item.get("Value")
#
#                 if name == "MpesaReceiptNumber":
#                     receipt = value
#                 elif name == "PhoneNumber":
#                     phone = normalize_phone(value)
#                 elif name == "Amount":
#                     amount = float(value)
#
#             if phone and amount:
#                 payment = Payment.objects.filter(phone_number=phone, amount=amount).exclude(status='success').last()
#                 if payment:
#                     if payment.status == 'success':
#                         return Response({"message": "Already processed"}, status=200)
#
#                     if result_code == 0:
#                         payment.status = 'success'
#                         payment.transaction_id = receipt
#
#                         # ✅ Generate ticket and save
#                         pdf_data = generate_ticket_pdf(payment.user, payment.event, receipt)
#                         payment.ticket.save(f"ticket_{payment.id}.pdf", ContentFile(pdf_data), save=True)
#                     else:
#                         payment.status = 'failed'
#
#                     payment.save()
#
#             return Response({"message": "Callback received"}, status=200)
#
#         except Exception as e:
#             return Response({"error": str(e)}, status=400)
#

# ✅ STK Push API View

class STKPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        phone = normalize_phone(request.data.get('phone'))
        event_id = request.data.get('event_id')

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        payment = Payment.objects.create(
            user=user,
            event=event,
            phone_number=phone,
            amount=event.price,
            status='pending'
        )

        callback_url = request.build_absolute_uri(reverse('payments:mpesa_callback'))

        response = lipa_na_mpesa(
            phone_number=phone,
            amount=event.price,
            account_reference=str(event.id),
            transaction_desc=f"Payment for {event.title}",
            callback_url=callback_url
        )

        return Response({
            "message": "STK Push initiated",
            "mpesa_response": response
        })
