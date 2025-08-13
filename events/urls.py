from django.urls import path
# from .views import EventListCreateView,process_payment,checkout,TestAuthView, EventListView, create_event,event_cards_view, event_detail, ticket_selection
from django.shortcuts import redirect
from . import views
def home_redirect(request):
    return redirect('events:event_cards')

app_name = 'events'

urlpatterns = [
    path('', views.event_cards_view, name='home'),  # Home page now shows cards
    path('test-auth/', views.TestAuthView.as_view()),
    path('create/', views.create_event, name='create_event'),
    path('cards/', views.event_cards_view, name='event_cards'),  # Optional, keep if you want /cards too
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/tickets/', views.ticket_selection, name='ticket_selection'),
    path('<int:event_id>/checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('', views.EventListCreateView.as_view(), name='event-list-create'),
    path('test-auth/', views.TestAuthView.as_view()),
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.create_event, name='create_event'),
    path('cards/', views.event_cards_view, name='event_cards'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/tickets/', views.ticket_selection, name='ticket_selection'),
    path('<int:event_id>/checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

]



# urlpatterns = [
#     path('', EventListCreateView.as_view(), name='event-list-create'),
#     path('test-auth/', TestAuthView.as_view()),
#     path('', EventListView.as_view(), name='event_list'),
#     path('create/', create_event, name='create_event'),
#     path('cards/', event_cards_view, name='event_cards'),
#     path('<int:pk>/', event_detail, name='event_detail'),
#     path('<int:event_id>/tickets/', ticket_selection, name='ticket_selection'),
#     path('<int:event_id>/checkout/', checkout, name='checkout'),
#     path('process-payment/', process_payment, name='process_payment'),
#
# ]
