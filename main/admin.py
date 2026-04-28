from django.contrib import admin

from .audit import log_audit_event
from .models import AnimationVideo, AuditLog, Category, Flipbook


admin.site.site_header = "Django administration"
admin.site.site_title = "CraftyKids Admin"
admin.site.index_title = "Site administration"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_audit_event(request, 'update' if change else 'create', obj, {'source': 'admin'})

    def delete_model(self, request, obj):
        log_audit_event(request, 'delete', obj, {'source': 'admin'})
        super().delete_model(request, obj)


@admin.register(AnimationVideo)
class AnimationVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "duration", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "description")
    autocomplete_fields = ("category",)
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_audit_event(request, 'update' if change else 'create', obj, {'source': 'admin'})

    def delete_model(self, request, obj):
        log_audit_event(request, 'delete', obj, {'source': 'admin'})
        super().delete_model(request, obj)


@admin.register(Flipbook)
class FlipbookAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "description")
    autocomplete_fields = ("category",)
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_audit_event(request, 'update' if change else 'create', obj, {'source': 'admin'})

    def delete_model(self, request, obj):
        log_audit_event(request, 'delete', obj, {'source': 'admin'})
        super().delete_model(request, obj)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'target_model', 'target_label', 'ip_address')
    list_filter = ('action', 'target_model', 'created_at')
    search_fields = ('message', 'target_label', 'actor__username', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = (
        'actor',
        'action',
        'target_model',
        'target_id',
        'target_label',
        'message',
        'metadata',
        'ip_address',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        return {}
