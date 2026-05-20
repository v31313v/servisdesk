from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.db import models
from accounts.models import UserProfile
from .models import Ticket, Comment, Notification
from .forms import TicketForm, CommentForm, TicketStatusForm
from .filters import TicketFilter


def get_manager_emails():
    manager_users = User.objects.filter(profile__role='manager', email__isnull=False)
    return [u.email for u in manager_users if u.email]


def create_notification(user, ticket, message):
    if user:
        Notification.objects.create(user=user, ticket=ticket, message=message)

@login_required
def get_tickets_by_status(request, status):
    # Для квадрата "В работе" показываем и "В работе", и "На доработке"
    if status == 'in_progress':
        status_filter = ['in_progress', 'rework']
    elif status == 'frozen':
        status_filter = ['frozen', 'closed']
    else:
        status_filter = [status]

    if request.user.profile.role == 'manager':
        tickets = Ticket.objects.filter(status__in=status_filter)
    else:
        tickets = Ticket.objects.filter(
            models.Q(author=request.user) | models.Q(assigned_to=request.user),
            status__in=status_filter
        ).distinct()

    return render(request, 'tickets/_ticket_table.html', {
        'tickets': tickets,
        'status': status,
    })

@login_required
def ticket_list(request):
    if request.user.profile.role == 'manager':
        base_qs = Ticket.objects.all()
    else:
        base_qs = Ticket.objects.filter(
            models.Q(author=request.user) | models.Q(assigned_to=request.user)
        ).distinct()

    # Для оператора скрываем закрытые
    if request.user.profile.role == 'operator':
        visible_qs = base_qs.exclude(status='closed')
    else:
        visible_qs = base_qs

    # Счётчики для квадратов
    new_count = base_qs.filter(status='new').count()
    in_progress_count = base_qs.filter(status='in_progress').count()
    resolved_count = base_qs.filter(status='resolved').count()
    frozen_count = base_qs.filter(status='frozen').count()

    total_count = visible_qs.count()

    ticket_filter = TicketFilter(request.GET, queryset=visible_qs)
    tickets = ticket_filter.qs

    sort = request.GET.get('sort', '-created_at')
    allowed_sorts = ['id', '-id', 'subject', '-subject', 'priority', '-priority',
                     'status', '-status', 'created_at', '-created_at', 'deadline', '-deadline']
    if sort in allowed_sorts:
        tickets = tickets.order_by(sort)

    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': ticket_filter,
        'tickets': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'new_count': new_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'frozen_count': frozen_count,
        'sort': sort,
    }
    return render(request, 'tickets/ticket_list.html', context)

    if request.user.profile.role == 'manager':
        tickets = Ticket.objects.all()
    else:
        tickets = Ticket.objects.filter(
            models.Q(author=request.user) | models.Q(assigned_to=request.user)
        ).distinct()

    ticket_filter = TicketFilter(request.GET, queryset=tickets)
    tickets = ticket_filter.qs

    sort = request.GET.get('sort', '-created_at')
    allowed_sorts = ['id', '-id', 'subject', '-subject', 'priority', '-priority',
                     'status', '-status', 'created_at', '-created_at', 'deadline', '-deadline']
    if sort in allowed_sorts:
        tickets = tickets.order_by(sort)

    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': ticket_filter,
        'tickets': page_obj,
        'page_obj': page_obj,
        'total_count': tickets.count(),
        'new_count': tickets.filter(status='new').count(),
        'in_progress_count': tickets.filter(status='in_progress').count(),
        'sort': sort,
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.user.profile.role == 'operator':
        if ticket.author != request.user and ticket.assigned_to != request.user:
            raise PermissionDenied('У вас нет доступа к этой заявке')

    # Отметить уведомление прочитанным
    notif_id = request.GET.get('read')
    if notif_id:
        Notification.objects.filter(id=notif_id, user=request.user).delete()

    if request.method == 'POST' and 'comment_submit' in request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен')
            return redirect('ticket_detail', pk=pk)
    else:
        comment_form = CommentForm()

    available_statuses = ticket.ALLOWED_TRANSITIONS.get(ticket.status, [])
    status_choices = [(s, dict(Ticket.STATUS_CHOICES)[s]) for s in available_statuses]
    status_form = TicketStatusForm()
    status_form.fields['status'].choices = [('', '---')] + status_choices

    context = {
        'ticket': ticket,
        'comment_form': comment_form,
        'status_form': status_form,
        'comments': ticket.comments.all(),
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.author = request.user
            ticket.save()
            messages.success(request, f'Заявка #{ticket.pk} создана')

            # Уведомление руководителям
            managers = User.objects.filter(profile__role='manager')
            for mgr in managers:
                create_notification(mgr, ticket, f'Новая заявка #{ticket.pk}: {ticket.subject}')

            # Уведомление исполнителю
            if ticket.assigned_to:
                create_notification(ticket.assigned_to, ticket, f'Вы назначены на заявку #{ticket.pk}')

            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, 'tickets/ticket_form.html', {
        'form': form,
        'action': 'Создание заявки'
    })


@login_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.user.profile.role == 'operator':
        if ticket.author != request.user:
            raise PermissionDenied('Вы не можете редактировать чужую заявку')
        if ticket.status != 'new':
            messages.error(request, 'Можно редактировать только новые заявки')
            return redirect('ticket_detail', pk=pk)

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f'Заявка #{pk} обновлена')
            return redirect('ticket_detail', pk=pk)
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'tickets/ticket_form.html', {
        'form': form,
        'action': f'Редактирование заявки #{pk}'
    })


@login_required
def ticket_delete(request, pk):
    if request.user.profile.role != 'manager':
        raise PermissionDenied('Только руководитель может удалять заявки')

    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        ticket_id = ticket.pk
        ticket.delete()
        messages.success(request, f'Заявка #{ticket_id} удалена')
        return redirect('ticket_list')
    return render(request, 'tickets/ticket_confirm_delete.html', {'ticket': ticket})


@login_required
def ticket_change_status(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = TicketStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            try:
                old_status = ticket.status
                ticket.change_status(new_status, request.user)
                messages.success(request,
                    f'Статус заявки #{pk} изменён на {ticket.get_status_display()}')

                # Уведомление руководителям
                managers = User.objects.filter(profile__role='manager')
                for mgr in managers:
                    create_notification(mgr, ticket,
                        f'Статус заявки #{ticket.pk} → {ticket.get_status_display()}')

                # Уведомление автору
                if ticket.author != request.user:
                    create_notification(ticket.author, ticket,
                        f'Статус вашей заявки #{ticket.pk} → {ticket.get_status_display()}')

                # Уведомление исполнителю при возврате на доработку
                if new_status == 'rework' and ticket.assigned_to:
                    create_notification(ticket.assigned_to, ticket,
                        f'Заявка #{ticket.pk} возвращена на доработку')

            except ValidationError as e:
                messages.error(request, str(e))
    return redirect('ticket_detail', pk=pk)