from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware, get_current_timezone
from .models import Notification

def notifications_processor(request):
    unread_count = 0
    
    last_seen_str = request.session.get('last_seen_notifications')
    
    if last_seen_str:
        try:
            last_seen = parse_datetime(last_seen_str)
            if last_seen and not is_aware(last_seen):
                last_seen = make_aware(last_seen, get_current_timezone())
            unread_count = Notification.objects.filter(created_at__gt=last_seen).count()
        except Exception:
            unread_count = Notification.objects.count()
    else:
        # If they've never seen notifications, they have unread if any exist
        unread_count = Notification.objects.count()
        
    return {
        'has_unread_notifications': unread_count > 0,
        'unread_notifications_count': unread_count
    }
