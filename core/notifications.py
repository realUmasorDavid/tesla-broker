from .models import Notification
 
def create_notification(profile, title, message, notif_type='general'):
    """Central helper — call this everywhere an event fires."""
    Notification.objects.create(
        profile    = profile,
        title      = title,
        message    = message,
        notif_type = notif_type,
    )