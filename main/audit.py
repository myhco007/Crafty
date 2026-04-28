from django.utils.text import Truncator

from .models import AuditLog


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit_event(request, action, target, metadata=None, target_label=None):
    actor = getattr(request, 'user', None)
    actor = actor if getattr(actor, 'is_authenticated', False) else None
    actor_name = actor.username if actor else 'System'
    target_model = target.__class__.__name__ if target is not None else 'System'
    resolved_target_label = target_label or (str(target) if target is not None else 'System')

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_model=target_model,
        target_id=getattr(target, 'pk', None),
        target_label=Truncator(resolved_target_label).chars(255),
        message=Truncator(f'{actor_name} {action} {resolved_target_label}').chars(255),
        metadata=metadata or {},
        ip_address=get_client_ip(request),
    )
