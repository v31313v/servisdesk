from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        unread_list = Notification.objects.filter(user=request.user, is_read=False)[:5]
        return {
            'unread_count': unread_count,
            'unread_notifications': unread_list,
        }
    return {}