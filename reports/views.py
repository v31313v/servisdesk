from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, F
from django.db.models import ExpressionWrapper, DurationField
from django.http import HttpResponse
from datetime import datetime, timedelta
from tickets.models import Ticket
import json
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def is_manager(user):
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role == 'manager'
    )


@login_required
@user_passes_test(is_manager, login_url='ticket_list')
def dashboard(request):
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    tickets = Ticket.objects.all()

    if date_from_str:
        tickets = tickets.filter(created_at__gte=date_from_str)
    if date_to_str:
        tickets = tickets.filter(created_at__lte=date_to_str + ' 23:59:59')

    if not date_from_str and not date_to_str:
        last_30 = datetime.now() - timedelta(days=30)
        tickets = tickets.filter(created_at__gte=last_30)

    # Проверка экспорта в Excel
    if request.GET.get('export') == 'excel':
        return export_excel(tickets, date_from_str, date_to_str)

    total = tickets.count()
    open_count = tickets.filter(status__in=['new', 'in_progress']).count()
    resolved_count = tickets.filter(status='resolved').count()
    closed_count = tickets.filter(status='closed').count()

    avg_resolution = None
    resolved_tickets = tickets.filter(status__in=['resolved', 'closed'])
    if resolved_tickets.exists():
        avg_duration = resolved_tickets.annotate(
            duration=ExpressionWrapper(
                F('updated_at') - F('created_at'),
                output_field=DurationField()
            )
        ).aggregate(avg=Avg('duration'))['avg']
        if avg_duration:
            avg_resolution = round(avg_duration.total_seconds() / 3600, 1)

    by_type = tickets.values('ticket_type__name').annotate(
        count=Count('id')
    ).order_by('-count')

    by_type_labels = json.dumps([
        item['ticket_type__name'] or 'Без типа' for item in by_type
    ])
    by_type_counts = json.dumps([item['count'] for item in by_type])

    by_status = tickets.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    status_labels = {k: v for k, v in Ticket.STATUS_CHOICES}
    by_status_labels = json.dumps([
        status_labels.get(item['status'], item['status']) for item in by_status
    ])
    by_status_counts = json.dumps([item['count'] for item in by_status])

    by_operator = tickets.values(
        'author__last_name', 'author__first_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'date_from': date_from_str,
        'date_to': date_to_str,
        'total': total,
        'open_count': open_count,
        'resolved_count': resolved_count,
        'closed_count': closed_count,
        'avg_resolution': avg_resolution,
        'by_type_labels': by_type_labels,
        'by_type_counts': by_type_counts,
        'by_status_labels': by_status_labels,
        'by_status_counts': by_status_counts,
        'by_operator': by_operator,
    }
    return render(request, 'reports/dashboard.html', context)


def export_excel(tickets, date_from, date_to):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Заявки"

    # Заголовки стилей
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="0d6efd", end_color="0d6efd", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

    # Заголовок отчёта
    ws.merge_cells('A1:K1')
    ws['A1'] = 'ООО «ПКБ "НЕВЕКС"» — Отчёт по заявкам'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:K2')
    period = f"Период: {date_from or '...'} — {date_to or '...'}"
    ws['A2'] = period
    ws['A2'].font = Font(size=10, italic=True)
    ws['A2'].alignment = Alignment(horizontal='center')

    # Шапка таблицы
    headers = [
        '№', 'Тема', 'Описание', 'Инициатор', 'Отдел',
        'Телефон', 'Email', 'Тип обращения', 'Проект',
        'Приоритет', 'Статус', 'Дата создания'
    ]
    col_widths = [5, 30, 40, 20, 20, 15, 25, 25, 25, 12, 12, 15]

    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center_align
        ws.column_dimensions[get_column_letter(col)].width = width

    # Данные
    priority_map = dict(Ticket.PRIORITY_CHOICES)
    status_map = dict(Ticket.STATUS_CHOICES)

    for idx, ticket in enumerate(tickets, 1):
        row = idx + 4
        data = [
            idx,
            ticket.subject,
            ticket.description,
            ticket.initiator,
            ticket.initiator_department,
            ticket.initiator_phone,
            ticket.initiator_email,
            ticket.ticket_type.name if ticket.ticket_type else '',
            ticket.project.code if ticket.project else '',
            priority_map.get(ticket.priority, ''),
            status_map.get(ticket.status, ''),
            ticket.created_at.strftime('%d.%m.%Y %H:%M') if ticket.created_at else ''
        ]
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center', wrap_text=True) if col > 2 else center_align

    # Итоговая строка
    summary_row = len(tickets) + 5
    ws.merge_cells(f'A{summary_row}:L{summary_row}')
    ws.cell(row=summary_row, column=1,
            value=f'Всего заявок: {tickets.count()}  |  '
                  f'Открыто: {tickets.filter(status__in=["new", "in_progress"]).count()}  |  '
                  f'Решено: {tickets.filter(status="resolved").count()}  |  '
                  f'Закрыто: {tickets.filter(status="closed").count()}'
    ).font = Font(bold=True)

    # Ответ
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'otchet_nevex_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response