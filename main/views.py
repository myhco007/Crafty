from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .audit import log_audit_event
from .models import AnimationVideo, AuditLog, Flipbook, Category, Announcement, Notification
from .forms import AnimationVideoForm, FlipbookForm, AnnouncementForm

def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def support_us(request):
    return render(request, 'main/support_us.html')

def faqs(request):
    return render(request, 'main/faqs.html')

from django.utils.timezone import now

def notifications(request):
    notifications_list = Notification.objects.all()
    
    # Update session to hide the indicator
    request.session['last_seen_notifications'] = now().isoformat()
    
    return render(request, 'main/notifications.html', {'notifications': notifications_list})


# Animation Videos CRUD

def video_list(request):
    category = request.GET.get('category')
    craft_category = request.GET.get('craft_category', 'All Categories')
    query = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', 'All Grades')
    
    videos = AnimationVideo.objects.filter(is_archived=False)
    
    if category:
        videos = videos.filter(category__name=category)
    
    if craft_category and craft_category != 'All Categories':
        videos = videos.filter(craft_category=craft_category)
        
    if grade and grade != 'All Grades':
        videos = videos.filter(grade=grade)
    
    if query:
        videos = videos.filter(title__icontains=query)
        
    return render(request, 'main/video_list.html', {'videos': videos, 'active': category, 'selected_grade': grade, 'selected_craft': craft_category})

def video_create(request):
    form = AnimationVideoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        video = form.save()
        log_audit_event(request, 'create', video, {'source': 'dashboard'})
        Notification.objects.create(
            title="New Video Uploaded",
            message=f"A new video tutorial '{video.title}' is now available in the {video.category.name} category.",
            icon="Video"
        )
        return redirect('video_list')
    return render(request, 'main/video_form.html', {'form': form, 'title': 'Add Video'})

def video_edit(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    form = AnimationVideoForm(request.POST or None, request.FILES or None, instance=video)
    if form.is_valid():
        updated_video = form.save()
        log_audit_event(request, 'update', updated_video, {'source': 'dashboard'})
        return redirect('video_list')
    return render(request, 'main/video_form.html', {'form': form, 'title': 'Edit Video'})

def video_delete(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    if request.method == 'POST':
        video.is_archived = True
        video.save()
        log_audit_event(request, 'archive', video, {'source': 'dashboard'})
        messages.success(request, 'Video archived successfully!')
        return redirect('video_list')
    return render(request, 'main/confirm_delete.html', {'object': video})


# Flipbooks CRUD

def flipbook_list(request):
    category = request.GET.get('category')
    craft_category = request.GET.get('craft_category', 'All Categories')
    query = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', 'All Grades')
    
    flipbooks = Flipbook.objects.filter(is_archived=False)
    
    if category:
        flipbooks = flipbooks.filter(category__name=category)
    
    if craft_category and craft_category != 'All Categories':
        flipbooks = flipbooks.filter(craft_category=craft_category)
        
    if grade and grade != 'All Grades':
        flipbooks = flipbooks.filter(grade=grade)
    
    if query:
        flipbooks = flipbooks.filter(title__icontains=query)
        
    return render(request, 'main/flipbook_list.html', {'flipbooks': flipbooks, 'active': category, 'selected_grade': grade, 'selected_craft': craft_category})

# DITO KO IDINAGDAG YUNG FLIPBOOK DETAIL VIEW
def flipbook_detail(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    return render(request, 'main/flipbook_detail.html', {'flipbook': flipbook})

def flipbook_create(request):
    form = FlipbookForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        flipbook = form.save()
        log_audit_event(request, 'create', flipbook, {'source': 'dashboard'})
        Notification.objects.create(
            title="New Flipbook Uploaded",
            message=f"A new flipbook tutorial '{flipbook.title}' is now available in the {flipbook.category.name} category.",
            icon="Book"
        )
        return redirect('flipbook_list')
    return render(request, 'main/flipbook_form.html', {'form': form, 'title': 'Add Flipbook'})

def flipbook_edit(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    form = FlipbookForm(request.POST or None, request.FILES or None, instance=flipbook)
    if form.is_valid():
        updated_flipbook = form.save()
        log_audit_event(request, 'update', updated_flipbook, {'source': 'dashboard'})
        return redirect('flipbook_list')
    return render(request, 'main/flipbook_form.html', {'form': form, 'title': 'Edit Flipbook'})

def flipbook_delete(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    if request.method == 'POST':
        flipbook.is_archived = True
        flipbook.save()
        log_audit_event(request, 'archive', flipbook, {'source': 'dashboard'})
        messages.success(request, 'Flipbook archived successfully!')
        return redirect('flipbook_list')
    return render(request, 'main/confirm_delete.html', {'object': flipbook})


# Auth

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            log_audit_event(request, 'login', user, {'source': 'auth'}, target_label=user.username)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'main/login.html')

def register_view(request):
    if request.method == 'POST':
        full_name  = request.POST.get('full_name')
        email      = request.POST.get('email')
        username   = request.POST.get('username')
        password1  = request.POST.get('password1')
        password2  = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            first, *last = full_name.split(' ', 1)
            user.first_name = first
            user.last_name = last[0] if last else ''
            user.save()
            login(request, user)
            log_audit_event(request, 'register', user, {'source': 'auth'}, target_label=user.username)
            return redirect('home')
    return render(request, 'main/register.html')

def logout_view(request):
    if request.user.is_authenticated:
        log_audit_event(request, 'logout', request.user, {'source': 'auth'}, target_label=request.user.username)
    logout(request)
    return redirect('home')


# Dashboard

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def dashboard(request):
    context = {
        'total_videos':     AnimationVideo.objects.filter(is_archived=False).count(),
        'total_flipbooks':  Flipbook.objects.filter(is_archived=False).count(),
        'total_users':      User.objects.count(),
        'total_categories': Category.objects.count(),
        'total_audit_logs': AuditLog.objects.count(),
        'recent_audit_logs': AuditLog.objects.select_related('actor')[:8],
        'recent_videos':    AnimationVideo.objects.filter(is_archived=False).order_by('-created_at')[:5],
        'recent_flipbooks': Flipbook.objects.filter(is_archived=False).order_by('-created_at')[:5],
        'all_videos':       AnimationVideo.objects.filter(is_archived=False).order_by('-created_at'),
        'all_flipbooks':    Flipbook.objects.filter(is_archived=False).order_by('-created_at'),
        'archived_videos':  AnimationVideo.objects.filter(is_archived=True).order_by('-created_at'),
        'archived_flipbooks': Flipbook.objects.filter(is_archived=True).order_by('-created_at'),
        'users':            User.objects.order_by('-date_joined'),
        'categories':       Category.objects.all(),
        'announcements':    Announcement.objects.all().order_by('-created_at'),
    }
    return render(request, 'main/dashboard.html', context)


# Category CRUD

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            if Category.objects.filter(name=name).exists():
                messages.error(request, 'Category already exists.')
            else:
                category = Category.objects.create(name=name)
                log_audit_event(request, 'create', category, {'source': 'dashboard'})
                messages.success(request, f'Category "{name}" created!')
        return redirect('dashboard')
    return redirect('dashboard')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            category.name = name
            category.save()
            log_audit_event(request, 'update', category, {'source': 'dashboard'})
            messages.success(request, f'Category updated to "{name}"!')
    return redirect('dashboard')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        log_audit_event(request, 'delete', category, {'source': 'dashboard'})
        category.delete()
        messages.success(request, 'Category deleted!')
    return redirect('dashboard')

def explore_subjects(request):
    return render(request, 'main/explore_subjects.html')

# Announcements CRUD

def announcement_list(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'main/announcement_list.html', {'announcements': announcements})


@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def announcement_create(request):
    form = AnnouncementForm(request.POST or None)
    if form.is_valid():
        announcement = form.save()
        log_audit_event(request, 'create', announcement, {'source': 'dashboard'})
        Notification.objects.create(
            title="New Announcement",
            message=announcement.title,
            icon="Note"
        )
        messages.success(request, 'Announcement created!')
        return redirect('dashboard')
    return render(request, 'main/announcement_form.html', {'form': form, 'title': 'Create Announcement'})


@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, instance=announcement)
    if form.is_valid():
        announcement = form.save()
        log_audit_event(request, 'update', announcement, {'source': 'dashboard'})
        messages.success(request, 'Announcement updated!')
        return redirect('dashboard')
    return render(request, 'main/announcement_form.html', {'form': form, 'title': 'Edit Announcement'})


@login_required(login_url='login')
@user_passes_test(is_admin, login_url='home')
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        log_audit_event(request, 'delete', announcement, {'source': 'dashboard'})
        announcement.delete()
        messages.success(request, 'Announcement deleted!')
        return redirect('dashboard')
    return render(request, 'main/confirm_delete.html', {'object': announcement})