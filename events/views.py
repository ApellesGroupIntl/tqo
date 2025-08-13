from django.shortcuts import render,redirect
from rest_framework import generics, permissions
from .models import Event
from .serializers import EventSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .forms import EventForm
from django.contrib.admin.views.decorators import staff_member_required
from .models import Event, TicketType
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from payments.mpesa import lipa_na_mpesa  # your integration function
from django.urls import reverse
# events/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, TicketType

@login_required
def ticket_selection(request, event_id):
    """
    Page where user selects ticket type & quantity.
    Stores selection in session and redirects to payments.checkout.
    """
    event = get_object_or_404(Event, id=event_id)
    ticket_types = TicketType.objects.filter(event=event)

    if request.method == "POST":
        ticket_id = request.POST.get("ticket_type")
        quantity = int(request.POST.get("quantity", 1))

        ticket = get_object_or_404(TicketType, id=ticket_id, event=event)

        # Save checkout data in session
        request.session['checkout_data'] = {
            'event_id': event.id,
            'event_title': event.title,
            'ticket_id': ticket.id,
            'ticket_name': ticket.name,
            'price_per_ticket': float(ticket.price),
            'quantity': quantity,
            'total_price': float(ticket.price) * quantity
        }

        # redirect to payments checkout (login required will not redirect because user already logged in)
        return redirect('payments:checkout', event_id=event.id)

    return render(request, 'events/ticket_selection.html', {
        'event': event,
        'ticket_types': ticket_types
    })




def event_checkout(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    ticket_types = TicketType.objects.filter(event=event)

    if request.method == "POST":
        phone = request.POST.get("phone")
        total_amount = float(request.POST.get("total_amount"))

        # Initiate M-Pesa payment
        response = lipa_na_mpesa(phone, total_amount, f"Tickets for {event.name}")

        if response.get("ResponseCode") == "0":
            return redirect(reverse("payment_success"))
        else:
            return redirect(reverse("payment_failed"))

    return render(request, "events/checkout.html", {
        "event": event,
        "ticket_types": ticket_types
    })

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'events/event_detail.html', {'event': event})

def checkout(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    ticket_type = request.GET.get('ticket_type', 'Regular')
    quantity = int(request.GET.get('quantity', 1))
    price = event.get_ticket_price(ticket_type)
    total = price * quantity

    return render(request, 'events/checkout.html', {
        'event': event,
        'ticket_type': ticket_type,
        'quantity': quantity,
        'total': total
    })

def process_payment(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        total = request.POST.get('total')
        # Here call M-Pesa STK Push function
        messages.success(request, "Payment initiated. Check your phone.")
        return redirect('event_detail', event_id=request.POST.get('event_id'))



# def checkout_view(request, event_id):
#     event = get_object_or_404(Event, id=event_id)
#     tickets = TicketType.objects.filter(event=event)
#
#     if request.method == "POST":
#         ticket_id = request.POST.get("ticket_id")
#         quantity = int(request.POST.get("quantity", 1))
#         ticket = get_object_or_404(TicketType, id=ticket_id)
#         total_price = ticket.price * quantity
#
#         return render(request, "checkout.html", {
#             "event": event,
#             "ticket": ticket,
#             "quantity": quantity,
#             "total_price": total_price
#         })
#     return render(request, 'events/checkout.html', {'event': event})
#
#     # return render(request, "select_ticket.html", {"event": event, "tickets": tickets})

# def ticket_selection(request, event_id):
#     event = get_object_or_404(Event, id=event_id)
#     return render(request, 'events/ticket_selection.html', {'event': event})
#



def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'events/event_detail.html', {'event': event})
def event_cards_view(request):
    events = Event.objects.all().order_by('date')
    return render(request, 'events/event_cards.html', {'events': events})
@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            return redirect('events:event_list')
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})


class TestAuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": request.user.username})


# Template-based view for event list
@method_decorator(login_required, name='dispatch')
class EventListView(View):
    def get(self, request):
        events = Event.objects.all().order_by('date')
        return render(request, 'events/event_list.html', {'events': events})

class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all().order_by('date')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')