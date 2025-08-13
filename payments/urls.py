from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import (
    buy_ticket,
    MpesaCallbackView,  InitiateSTKPushView,
    MpesaCallbackView,
    PaymentStatusView,
    payment_success, STKPushView,
    DownloadTicketView, preview_ticket, my_tickets, checkout,mpesa_payment,check_payment_status,
    InitiateSTKPushView, payment_success,
)

app_name = 'payments'


urlpatterns = [
    path('<int:event_id>/checkout/', views.checkout, name='checkout'),
    path("initiate-stk-push/", login_required(InitiateSTKPushView.as_view()), name="initiate-stk-push"),
    # path('initiate-stk-push/', views.initiate_stk_push, name='initiate_stk_push'),
    # path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    # path('payment-status/', views.payment_status, name='payment_status'),
    # path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('preview/<int:payment_id>/', views.preview_ticket, name='preview_ticket'),
    path('buy/<int:event_id>/', buy_ticket, name='buy_ticket'),
    path('callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('api/stk-push/', STKPushView.as_view(), name='stk_push'),
    path('download/<int:payment_id>/', DownloadTicketView.as_view(), name='download_ticket'),
    path('preview/<int:payment_id>/', preview_ticket, name='preview_ticket'),
    path('my-tickets/', my_tickets, name='my_tickets'),
    path('<int:event_id>/checkout/', checkout, name='checkout'),
    path('success/<str:transaction_id>/', payment_success, name='payment_success'),
    path('check-status/', check_payment_status, name='check_payment_status'),
    path('<int:event_id>/pay/', mpesa_payment, name='mpesa_payment'),
    # path('initiate-stk-push/', InitiateSTKPushView, name='initiate_stk_push'),
    # path('initiate-stk-push/', InitiateSTKPushView.as_view(), name='initiate_stk_push'),

    path('initiate-stk-push/', InitiateSTKPushView.as_view(), name='initiate_stk_push'),
    path('callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('check-status/', PaymentStatusView.as_view(), name='check_status'),
    path('success/<str:transaction_id>/', payment_success, name='payment_success'),
    path('mpesa-payment/', mpesa_payment, name='mpesa_payment'),
    path('<int:event_id>/payments/', mpesa_payment, name='mpesa_payment'),

]
