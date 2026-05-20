from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/edit/', views.ticket_edit, name='ticket_edit'),
    path('<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
    path('<int:pk>/change-status/', views.ticket_change_status, name='ticket_change_status'),
    path('api/<str:status>/', views.get_tickets_by_status, name='tickets_by_status'),
]