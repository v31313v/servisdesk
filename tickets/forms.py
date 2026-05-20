from django import forms
from django.contrib.auth.models import User
from .models import Ticket, Comment
from django.contrib.auth.models import User
import re

class TicketForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='operator'),
        required=False,
        label='Исполнитель',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Ticket
        fields = [
            'subject', 'description', 'initiator', 'initiator_department',
            'initiator_phone', 'initiator_email', 'ticket_type', 'project',
            'document_number', 'priority', 'deadline', 'assigned_to'
        ]
        labels = {
            'subject': 'Тема обращения',
            'description': 'Описание',
            'initiator': 'Инициатор (ФИО)',
            'initiator_department': 'Отдел инициатора',
            'initiator_phone': 'Телефон инициатора',
            'initiator_email': 'Email инициатора',
            'ticket_type': 'Тип обращения',
            'project': 'Проект',
            'document_number': '№ документа / чертежа',
            'priority': 'Приоритет',
            'deadline': 'Срок исполнения',
        }
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кратко опишите суть обращения'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Подробно опишите задачу, приложите ссылки на документацию'
            }),
            'initiator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Иванов Иван Иванович'
            }),
            'initiator_department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Конструкторский отдел'
            }),
            'initiator_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+79991234567'
            }),
            'initiator_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ivanov@nevex.ru'
            }),
            'ticket_type': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'НВК-2024-КЖ-045'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '')
        if len(subject.strip()) < 5:
            raise forms.ValidationError('Тема должна содержать минимум 5 символов')
        return subject.strip()

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description.strip()) < 10:
            raise forms.ValidationError('Описание должно содержать минимум 10 символов')
        return description.strip()

    def clean_initiator_phone(self):
        phone = self.cleaned_data.get('initiator_phone', '')
        if phone:
            phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not re.match(r'^\+7\d{10}$', phone_clean):
                raise forms.ValidationError('Формат телефона: +7XXXXXXXXXX (11 цифр, начиная с +7)')
            return phone_clean
        return phone

    def clean_initiator_email(self):
        email = self.cleaned_data.get('initiator_email', '')
        if email and '@' not in email:
            raise forms.ValidationError('Введите корректный email-адрес')
        return email


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': ''}
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Добавьте комментарий...'
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        if len(text.strip()) < 2:
            raise forms.ValidationError('Комментарий не может быть пустым')
        return text.strip()


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', '---')] + Ticket.STATUS_CHOICES,
        label='Новый статус',
        widget=forms.Select(attrs={'class': 'form-select'})
    )