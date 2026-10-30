from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Q
from .models import Notification

def is_super_admin(user):
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'SUPER_ADMIN'))

def get_user_notifications(user):
    if not user.is_authenticated:
        return Notification.objects.none()

    qs = Notification.objects.all()

    if is_super_admin(user):
        return qs

    # For registered regular users:
    # 1. 1 week (7 days) expiry rule: notifications older than 7 days disappear
    one_week_ago = now() - timedelta(days=7)
    qs = qs.filter(created_at__gte=one_week_ago)

    # 2. Exclude admin-only notifications
    qs = qs.exclude(title__icontains='Pending').exclude(title__icontains='Registration')

    # 3. Only show targeted notifications for this user OR global notifications created AFTER user registered
    user_joined = user.date_joined
    qs = qs.filter(
        Q(recipient=user) |
        Q(recipient__isnull=True, created_at__gte=user_joined)
    )

    # 4. If user has no targeted welcome notification yet, create 1 welcome notification
    if not Notification.objects.filter(recipient=user, title__icontains='Welcome').exists():
        first_name = user.first_name or user.username
        Notification.objects.create(
            recipient=user,
            title="Welcome to CraftyKids! 🎉",
            message=f"Congratulations, {first_name}! Your account has been officially approved by the Main Admin. Welcome to your creative space! Explore our fun DIY video tutorials, interactive flipbooks, and activities to get started.",
            icon="Star",
            link_url="/home/"
        )
        # Re-fetch after creation
        qs = Notification.objects.filter(created_at__gte=one_week_ago).exclude(
            title__icontains='Pending'
        ).exclude(title__icontains='Registration').filter(
            Q(recipient=user) | Q(recipient__isnull=True, created_at__gte=user_joined)
        )

    return qs

def notifications_processor(request):
    if not request.user.is_authenticated:
        return {
            'has_unread_notifications': False,
            'unread_notifications_count': 0
        }

    qs = get_user_notifications(request.user)

    if is_super_admin(request.user):
        unread_count = qs.count()
    else:
        last_seen = None
        if hasattr(request.user, 'profile') and request.user.profile.last_seen_notifications:
            last_seen = request.user.profile.last_seen_notifications

        if last_seen:
            unread_count = qs.filter(created_at__gt=last_seen).count()
        else:
            unread_count = qs.count()

    return {
        'has_unread_notifications': unread_count > 0,
        'unread_notifications_count': unread_count
    }
