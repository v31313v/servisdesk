from django.contrib import admin
from .models import Ticket, TicketType, Project, Comment, Notification

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'department']
    search_fields = ['name']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'client', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'status', 'priority', 'author', 'assigned_to', 'deadline', 'created_at']
    list_filter = ['status', 'priority', 'ticket_type', 'project']
    search_fields = ['subject', 'description', 'initiator']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read']