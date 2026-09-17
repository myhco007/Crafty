from django.urls import path
from . import views

urlpatterns = [
    # Existing
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('support-us/', views.support_us, name='support_us'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/cancel-grade/', views.cancel_grade_request, name='cancel_grade_request'),
    path('profile/verify-password/', views.verify_password_ajax, name='verify_password_ajax'),
    path('profile/update-password/', views.update_password_ajax, name='update_password_ajax'),
    path('faqs/', views.faqs, name='faqs'),
    path('notifications/', views.notifications, name='notifications'),
    path('calendar/', views.student_calendar, name='calendar'),
    path('activity/complete/', views.mark_completed, name='mark_completed'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('login/teacher/', views.login_view, {'template_name': 'main/teacher_login.html'}, name='teacher_login'),
    path('register/', views.register_view, name='register'),
    path('register/teacher/', views.teacher_register_view, name='teacher_register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Forgot Password
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code_view, name='verify_reset_code'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    # Animation Videos CRUD
    path('videos/', views.video_list, name='video_list'),
    path('videos/create/', views.video_create, name='video_create'),
    path('videos/<int:pk>/edit/', views.video_edit, name='video_edit'),
    path('videos/<int:pk>/delete/', views.video_delete, name='video_delete'),
    path('videos/<int:pk>/restore/', views.video_restore, name='video_restore'),
    path('videos/<int:pk>/permanent_delete/', views.video_permanent_delete, name='video_permanent_delete'),
    path('video/<int:pk>/', views.video_detail, name='video_detail'),
    path('video/<int:pk>/like/', views.video_like, name='video_like'),
    path('video/<int:pk>/comment/', views.video_comment, name='video_comment'),
    path('video/comment/<int:pk>/delete/', views.video_comment_delete, name='video_comment_delete'),

    # Flipbook CRUD
    path('flipbooks/', views.flipbook_list, name='flipbook_list'),
    path('flipbooks/create/', views.flipbook_create, name='flipbook_create'),
    path('flipbooks/<int:pk>/edit/', views.flipbook_edit, name='flipbook_edit'),
    path('flipbooks/<int:pk>/delete/', views.flipbook_delete, name='flipbook_delete'),
    path('flipbooks/<int:pk>/restore/', views.flipbook_restore, name='flipbook_restore'),
    path('flipbooks/<int:pk>/permanent_delete/', views.flipbook_permanent_delete, name='flipbook_permanent_delete'),
    path('flipbook/<int:pk>/', views.flipbook_detail, name='flipbook_detail'),
    path('flipbook/<int:pk>/like/', views.flipbook_like, name='flipbook_like'),
    path('flipbook/<int:pk>/comment/', views.flipbook_comment, name='flipbook_comment'),
    path('flipbook/comment/<int:pk>/delete/', views.flipbook_comment_delete, name='flipbook_comment_delete'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/approve/user/<int:pk>/', views.approve_user, name='approve_user'),
    path('dashboard/reject/user/<int:pk>/', views.reject_user, name='reject_user'),
    path('dashboard/approve/grade/<int:pk>/', views.approve_grade, name='approve_grade'),
    path('dashboard/reject/grade/<int:pk>/', views.reject_grade, name='reject_grade'),
    path('dashboard/approve/<str:model_type>/<int:pk>/', views.approve_content, name='approve_content'),
    path('dashboard/user/<int:pk>/toggle_status/', views.toggle_user_status, name='toggle_user_status'),
    path('dashboard/user/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('dashboard/user/<int:pk>/restore/', views.user_restore, name='user_restore'),
    path('dashboard/user/<int:pk>/permanent_delete/', views.user_permanent_delete, name='user_permanent_delete'),

    # Category CRUD
    path('dashboard/category/create/', views.category_create, name='category_create'),
    path('dashboard/category/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('dashboard/category/<int:pk>/delete/', views.category_delete, name='category_delete'),

    path('explore/', views.explore_subjects, name='explore_subjects'),

    # Announcements CRUD
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<int:pk>/increment-view/', views.increment_announcement_views, name='increment_announcement_views'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('announcements/<int:pk>/restore/', views.announcement_restore, name='announcement_restore'),
    path('announcements/<int:pk>/permanent_delete/', views.announcement_permanent_delete, name='announcement_permanent_delete'),
    
    # Calendar Events CRUD
    path('dashboard/calendar/create/', views.calendar_event_create, name='calendar_event_create'),
    path('dashboard/calendar/<int:pk>/edit/', views.calendar_event_edit, name='calendar_event_edit'),
    path('dashboard/calendar/<int:pk>/delete/', views.calendar_event_delete, name='calendar_event_delete'),
    path('dashboard/calendar/<int:pk>/restore/', views.calendar_event_restore, name='calendar_event_restore'),
    path('dashboard/calendar/<int:pk>/permanent_delete/', views.calendar_event_permanent_delete, name='calendar_event_permanent_delete'),
    
    # Teacher Tasks API
    path('api/tasks/create/', views.task_create_api, name='task_create_api'),
    path('api/tasks/<int:task_id>/update/', views.task_update_api, name='task_update_api'),
    path('api/tasks/<int:task_id>/delete/', views.task_delete_api, name='task_delete_api'),
    
    # Bulk Action
    path('dashboard/archive/bulk-action/', views.bulk_archive_action, name='bulk_archive_action'),
    path('dashboard/approve/bulk-action/', views.bulk_approval_action, name='bulk_approval_action'),
    path('dashboard/announcements/bulk-archive/', views.bulk_archive_announcements, name='bulk_archive_announcements'),
]
