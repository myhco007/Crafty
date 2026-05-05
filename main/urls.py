from django.urls import path
from . import views

urlpatterns = [
    # Existing
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('support-us/', views.support_us, name='support_us'),
    path('profile/', views.profile_view, name='profile'),
    path('faqs/', views.faqs, name='faqs'),
    path('notifications/', views.notifications, name='notifications'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('login/teacher/', views.login_view, {'template_name': 'main/teacher_login.html'}, name='teacher_login'),
    path('register/', views.register_view, name='register'),
    path('register/teacher/', views.teacher_register_view, name='teacher_register'),
    path('logout/', views.logout_view, name='logout'),

    # Animation Videos CRUD
    path('videos/', views.video_list, name='video_list'),
    path('videos/create/', views.video_create, name='video_create'),
    path('videos/<int:pk>/edit/', views.video_edit, name='video_edit'),
    path('videos/<int:pk>/delete/', views.video_delete, name='video_delete'),
    path('video/<int:pk>/', views.video_detail, name='video_detail'),
    path('video/<int:pk>/like/', views.video_like, name='video_like'),
    path('video/<int:pk>/comment/', views.video_comment, name='video_comment'),

    # Flipbook CRUD
    path('flipbooks/', views.flipbook_list, name='flipbook_list'),
    path('flipbooks/create/', views.flipbook_create, name='flipbook_create'),
    path('flipbooks/<int:pk>/edit/', views.flipbook_edit, name='flipbook_edit'),
    path('flipbooks/<int:pk>/delete/', views.flipbook_delete, name='flipbook_delete'),
    path('flipbook/<int:pk>/', views.flipbook_detail, name='flipbook_detail'),
    path('flipbook/<int:pk>/like/', views.flipbook_like, name='flipbook_like'),
    path('flipbook/<int:pk>/comment/', views.flipbook_comment, name='flipbook_comment'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/approve/teacher/<int:pk>/', views.approve_teacher, name='approve_teacher'),
    path('dashboard/approve/<str:model_type>/<int:pk>/', views.approve_content, name='approve_content'),
    path('dashboard/user/<int:pk>/toggle_status/', views.toggle_user_status, name='toggle_user_status'),
    path('dashboard/user/<int:pk>/delete/', views.delete_user, name='delete_user'),

    # Category CRUD
    path('dashboard/category/create/', views.category_create, name='category_create'),
    path('dashboard/category/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('dashboard/category/<int:pk>/delete/', views.category_delete, name='category_delete'),

    path('explore/', views.explore_subjects, name='explore_subjects'),

    # Announcements CRUD
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
]
