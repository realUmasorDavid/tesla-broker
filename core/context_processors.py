from .models import Notification
 
def notifications_processor(request):
    """Injects unread_notif_count and latest 5 notifications into every template."""
    if not request.user.is_authenticated:
        return {
            'unread_notif_count': 0,
            'recent_notifications': [],
        }
    try:
        profile = request.user.profile
        unread_notif_count   = Notification.objects.filter(profile=profile, is_read=False).count()
        recent_notifications = Notification.objects.filter(profile=profile)[:5]
        return {
            'unread_notif_count':   unread_notif_count,
            'recent_notifications': recent_notifications,
        }
    except Exception:
        return {
            'unread_notif_count': 0,
            'recent_notifications': [],
        }