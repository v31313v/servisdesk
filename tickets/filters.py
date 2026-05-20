import django_filters
from django import forms
from django.db import models
from .models import Ticket, TicketType


class TicketFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по теме, описанию, инициатору...'
        })
    )
    status = django_filters.ChoiceFilter(
        choices=[('', 'Все статусы')] + Ticket.STATUS_CHOICES,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ticket_type = django_filters.ModelChoiceFilter(
        queryset=TicketType.objects.all(),
        label='Тип обращения',
        empty_label='Все типы',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Дата с',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Дата по',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = Ticket
        fields = ['status', 'ticket_type', 'priority']

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                models.Q(subject__icontains=value) |
                models.Q(description__icontains=value) |
                models.Q(initiator__icontains=value)
            )
        return queryset