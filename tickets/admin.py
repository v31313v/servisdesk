from django.contrib import admin
from .models import TicketType, Project, Ticket, Comment

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
    list_display = ['id', 'subject', 'status', 'priority', 'author', 'created_at']
    list_filter = ['status', 'priority', 'ticket_type']
    search_fields = ['subject', 'description']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'created_at']