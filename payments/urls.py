from django.urls import path
from . import views
from .views import (
    buy_ticket,
    MpesaCallbackView,
    # InitiateSTKPushView,
    PaymentStatusView,
    payment_success,
    STKPushView,
    DownloadTicketView,
    preview_ticket,
    my_tickets,
    checkout,
    mpesa_payment,
    payment_status,
    stk_callback,
)

app_name = 'payments'

urlpatterns = [
    # Payment initiation
    # path('initiate-stk-push/', InitiateSTKPushView.as_view(), name='initiate_stk_push'),
    path('api/stk-push/', STKPushView.as_view(), name='stk_push'),

    # M-Pesa Callbacks
    # path("callback/", views.mpesa_callback, name="mpesa-callback"),
    # path('stk-callback/', stk_push_callback, name='stk_callback'),
    # path("stk-push/", views.initiate_stk_push, name="stk-push"),
    # path("stk-callback/", views.stk_callback, name="stk-callback"),

    # STK Push initiation
    path("stk-push/", views.initiate_stk_push, name="stk-push"),

    # M-Pesa callback URL (called by Safaricom)
    path("mpesa-callback/", views.mpesa_callback, name="mpesa-callback"),

    # Check payment status (for frontend polling)
    path("status/", views.payment_status, name="payment-status"),

    # Status checks
    # path('status/', PaymentStatusView.as_view(), name='payment_status'),
    path('check-status/', payment_status, name='payment_status'),

    # Success & Ticket management
    path('success/<str:transaction_id>/', payment_success, name='payment_success'),
    path('my-tickets/', my_tickets, name='my_tickets'),
    path('download/<int:payment_id>/', DownloadTicketView.as_view(), name='download_ticket'),
    path('preview/<int:payment_id>/', preview_ticket, name='preview_ticket'),

    # Checkout & direct payments
    path('<int:event_id>/checkout/', checkout, name='checkout'),
    path('buy/<int:event_id>/', buy_ticket, name='buy_ticket'),
    path('<int:event_id>/pay/', mpesa_payment, name='mpesa_payment'),
    path('mpesa-payment/', mpesa_payment, name='mpesa_payment'),
]
