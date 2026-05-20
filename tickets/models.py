from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import date
import re


class TicketType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Тип обращения')
    department = models.CharField(max_length=100, blank=True, verbose_name='Ответственный отдел')

    class Meta:
        verbose_name = 'Тип обращения'
        verbose_name_plural = 'Типы обращений'
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name='Шифр проекта')
    name = models.CharField(max_length=300, verbose_name='Наименование проекта')
    client = models.CharField(max_length=200, blank=True, verbose_name='Заказчик')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.name}'


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('frozen', 'Заморожена'),
        ('rework', 'На доработке'),
        ('resolved', 'Решена'),
        ('closed', 'Закрыта'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    ALLOWED_TRANSITIONS = {
        'new': ['in_progress', 'frozen', 'closed'],
        'in_progress': ['frozen', 'resolved', 'rework'],
        'frozen': ['in_progress', 'closed'],
        'rework': ['in_progress'],
        'resolved': ['closed', 'rework'],
        'closed': [],
    }

    subject = models.CharField(max_length=200, verbose_name='Тема обращения')
    description = models.TextField(verbose_name='Описание проблемы')
    initiator = models.CharField(max_length=150, verbose_name='Инициатор (ФИО)')
    initiator_department = models.CharField(max_length=100, blank=True, verbose_name='Отдел инициатора')
    initiator_phone = models.CharField(max_length=18, blank=True, verbose_name='Телефон инициатора')
    initiator_email = models.EmailField(blank=True, verbose_name='Email инициатора')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, null=True, verbose_name='Тип обращения')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Проект')
    document_number = models.CharField(max_length=50, blank=True, verbose_name='№ документа / чертежа')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets', verbose_name='Автор заявки')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name='Исполнитель')
    deadline = models.DateField(null=True, blank=True, verbose_name='Срок исполнения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заявка #{self.pk}: {self.subject}'

    def get_absolute_url(self):
        return reverse('ticket_detail', kwargs={'pk': self.pk})

    def clean(self):
        if self.initiator_phone:
            phone_clean = self.initiator_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not re.match(r'^\+7\d{10}$', phone_clean):
                raise ValidationError({'initiator_phone': 'Формат телефона: +7XXXXXXXXXX (11 цифр)'})

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def change_status(self, new_status, user):
        if not self.can_transition_to(new_status):
            status_labels = dict(self.STATUS_CHOICES)
            raise ValidationError(
                f'Недопустимый переход: {status_labels.get(self.status)} → {status_labels.get(new_status)}'
            )
        self.status = new_status
        if new_status in ['in_progress', 'resolved']:
            self.assigned_to = user
        self.save()

    @property
    def status_badge_class(self):
        classes = {
            'new': 'badge bg-light text-dark',
            'in_progress': 'badge bg-primary',
            'frozen': 'badge bg-light text-dark',
            'rework': 'badge bg-warning text-dark',
            'resolved': 'badge bg-success',
            'closed': 'badge bg-light text-dark',
        }
        return classes.get(self.status, 'badge bg-light')

    @property
    def priority_badge_class(self):
        classes = {
            'low': 'badge bg-light text-dark',
            'medium': 'badge bg-primary',
            'high': 'badge bg-warning text-dark',
            'critical': 'badge bg-danger',
        }
        return classes.get(self.priority, 'badge bg-light')

    @property
    def is_overdue(self):
        if self.deadline and self.status != 'closed':
            return date.today() > self.deadline
        return False


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments', verbose_name='Заявка')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def __str__(self):
        return f'Комментарий к #{self.ticket.pk} от {self.author.username}'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='Кому')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, verbose_name='Заявка')
    message = models.CharField(max_length=300, verbose_name='Текст')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.message[:50]}'