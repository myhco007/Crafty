from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware, get_current_timezone
from .models import Notification

def is_super_admin(user):
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'SUPER_ADMIN'))

def notifications_processor(request):
    unread_count = 0
    qs = Notification.objects.all()
    
    # Filter admin-only notifications for regular users
    if not is_super_admin(request.user):
        qs = qs.exclude(title__icontains='Pending').exclude(title__icontains='Registration')
    
    if not request.user.is_authenticated:
        return {
            'has_unread_notifications': False,
            'unread_notifications_count': 0
        }

    last_seen = None
    if hasattr(request.user, 'profile') and request.user.profile.last_seen_notifications:
        last_seen = request.user.profile.last_seen_notifications
        
    if last_seen:
        unread_count = qs.filter(created_at__gt=last_seen).count()
    else:
        # If they've never seen notifications, they have unread if any exist
        unread_count = qs.count()
        
    return {
        'has_unread_notifications': unread_count > 0,
        'unread_notifications_count': unread_count
    }
