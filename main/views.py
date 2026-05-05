from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .audit import log_audit_event
from .models import AnimationVideo, AuditLog, Flipbook, Category, Announcement, Notification, Comment, UserProfile
from .forms import AnimationVideoForm, FlipbookForm, AnnouncementForm, UserUpdateForm, UserProfileUpdateForm

# Helpers
def is_staff_or_teacher(user):
    return user.is_authenticated and (user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'TEACHER'))

def is_super_admin(user):
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'SUPER_ADMIN'))

def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def support_us(request):
    return render(request, 'main/support_us.html')

@login_required(login_url='login')
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileUpdateForm(instance=request.user.profile)
        
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'main/profile.html', context)

def faqs(request):
    return render(request, 'main/faqs.html')

from django.utils.timezone import now

def notifications(request):
    qs = Notification.objects.all()
    
    # Filter admin-only notifications for regular users
    if not is_super_admin(request.user):
        qs = qs.exclude(title__icontains='Pending').exclude(title__icontains='Registration')
        
    notifications_list = qs
    
    # Update session to hide the indicator
    request.session['last_seen_notifications'] = now().isoformat()
    
    return render(request, 'main/notifications.html', {'notifications': notifications_list})


# Animation Videos CRUD

def video_list(request):
    category = request.GET.get('category')
    craft_category = request.GET.get('craft_category', 'All Categories')
    query = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', 'All Grades')
    
    videos = AnimationVideo.objects.filter(is_archived=False, is_approved=True)
    
    if category:
        videos = videos.filter(category__name=category)
    
    if craft_category and craft_category != 'All Categories':
        videos = videos.filter(craft_category=craft_category)
        
    if grade and grade != 'All Grades':
        videos = videos.filter(grade=grade)
    
    if query:
        videos = videos.filter(title__icontains=query)
        
    return render(request, 'main/video_list.html', {'videos': videos, 'active': category, 'selected_grade': grade, 'selected_craft': craft_category})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def video_create(request):
    form = AnimationVideoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        video = form.save(commit=False)
        video.author = request.user
        
        # If teacher, needs approval
        if request.user.profile.role == 'TEACHER':
            video.is_approved = False
            video.save()
            form.save_m2m()
            log_audit_event(request, 'create', video, {'source': 'dashboard', 'status': 'pending'})
            Notification.objects.create(
                title="New Video Pending Approval",
                message=f"Teacher {request.user.username} uploaded a video '{video.title}' that needs approval.",
                icon="Video",
                link_url="/dashboard/"
            )
            messages.info(request, 'Video uploaded! It will be visible once the Main Admin approves it.')
        else:
            video.is_approved = True
            video.save()
            form.save_m2m()
            log_audit_event(request, 'create', video, {'source': 'dashboard', 'status': 'approved'})
            Notification.objects.create(
                title="New Video Uploaded",
                message=f"A new video tutorial '{video.title}' is now available.",
                icon="Video"
            )
        return redirect('dashboard' if request.user.is_staff else 'video_list')
    return render(request, 'main/video_form.html', {'form': form, 'title': 'Add Video'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def video_edit(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    form = AnimationVideoForm(request.POST or None, request.FILES or None, instance=video)
    if form.is_valid():
        updated_video = form.save()
        log_audit_event(request, 'update', updated_video, {'source': 'dashboard'})
        return redirect('video_list')
    return render(request, 'main/video_form.html', {'form': form, 'title': 'Edit Video'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def video_delete(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    if request.method == 'POST':
        video.is_archived = True
        video.save()
        log_audit_event(request, 'archive', video, {'source': 'dashboard'})
        messages.success(request, 'Video archived successfully!')
        return redirect('video_list')
    return render(request, 'main/confirm_delete.html', {'object': video})
    
def video_detail(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk, is_archived=False)
    comments = video.comments.all()
    has_liked = request.user.is_authenticated and video.liked_by.filter(id=request.user.id).exists()
    return render(request, 'main/video_detail.html', {'video': video, 'comments': comments, 'has_liked': has_liked})

@login_required(login_url='login')
def video_like(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    user = request.user
    if video.liked_by.filter(id=user.id).exists():
        video.liked_by.remove(user)
        liked = False
    else:
        video.liked_by.add(user)
        liked = True
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'count': video.liked_by.count()
        })
    return redirect('video_detail', pk=pk)

@login_required(login_url='login')
def video_comment(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', 'Anonymous').strip() or 'Anonymous'
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(video=video, name=name, text=text)
    return redirect('video_detail', pk=pk)


# Flipbooks CRUD

def flipbook_list(request):
    category = request.GET.get('category')
    craft_category = request.GET.get('craft_category', 'All Categories')
    query = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', 'All Grades')
    
    flipbooks = Flipbook.objects.filter(is_archived=False, is_approved=True)
    
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
    flipbook = get_object_or_404(Flipbook, pk=pk, is_archived=False)
    comments = flipbook.comments.all()
    has_liked = request.user.is_authenticated and flipbook.liked_by.filter(id=request.user.id).exists()
    return render(request, 'main/flipbook_detail.html', {'flipbook': flipbook, 'comments': comments, 'has_liked': has_liked})

@login_required(login_url='login')
def flipbook_like(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    user = request.user
    if flipbook.liked_by.filter(id=user.id).exists():
        flipbook.liked_by.remove(user)
        liked = False
    else:
        flipbook.liked_by.add(user)
        liked = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'count': flipbook.liked_by.count()
        })
    return redirect('flipbook_detail', pk=pk)

@login_required(login_url='login')
def flipbook_comment(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', 'Anonymous').strip() or 'Anonymous'
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(flipbook=flipbook, name=name, text=text)
    return redirect('flipbook_detail', pk=pk)

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def flipbook_create(request):
    form = FlipbookForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        flipbook = form.save(commit=False)
        flipbook.author = request.user
        
        if request.user.profile.role == 'TEACHER':
            flipbook.is_approved = False
            flipbook.save()
            form.save_m2m()
            log_audit_event(request, 'create', flipbook, {'source': 'dashboard', 'status': 'pending'})
            Notification.objects.create(
                title="New Flipbook Pending Approval",
                message=f"Teacher {request.user.username} uploaded a flipbook '{flipbook.title}' that needs approval.",
                icon="Book",
                link_url="/dashboard/"
            )
            messages.info(request, 'Flipbook uploaded! It will be visible once approved.')
        else:
            flipbook.is_approved = True
            flipbook.save()
            form.save_m2m()
            log_audit_event(request, 'create', flipbook, {'source': 'dashboard', 'status': 'approved'})
            Notification.objects.create(
                title="New Flipbook Uploaded",
                message=f"A new flipbook tutorial '{flipbook.title}' is now available.",
                icon="Book"
            )
        return redirect('dashboard' if request.user.is_staff else 'flipbook_list')
    return render(request, 'main/flipbook_form.html', {'form': form, 'title': 'Add Flipbook'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def flipbook_edit(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    form = FlipbookForm(request.POST or None, request.FILES or None, instance=flipbook)
    if form.is_valid():
        updated_flipbook = form.save()
        log_audit_event(request, 'update', updated_flipbook, {'source': 'dashboard'})
        return redirect('flipbook_list')
    return render(request, 'main/flipbook_form.html', {'form': form, 'title': 'Edit Flipbook'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
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

def login_view(request, template_name='main/login.html'):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.profile.role == 'TEACHER' and not user.profile.is_approved:
                messages.error(request, 'Your teacher account is pending approval from the Main Admin.')
                return render(request, template_name)
            
            login(request, user)
            log_audit_event(request, 'login', user, {'source': 'auth'}, target_label=user.username)
            
            if user.profile.role in ['SUPER_ADMIN', 'TEACHER']:
                return redirect('dashboard')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, template_name)

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
            
            # Profile defaults to CLIENT, which is correct here
            login(request, user)
            log_audit_event(request, 'register', user, {'source': 'auth'}, target_label=user.username)
            return redirect('home')
    return render(request, 'main/register.html')

def teacher_register_view(request):
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
            
            # Set role to TEACHER and is_approved to False
            user.profile.role = 'TEACHER'
            user.profile.is_approved = False
            user.profile.save()
            
            log_audit_event(request, 'register', user, {'source': 'teacher_auth'}, target_label=user.username)
            
            # Notify Super Admin
            Notification.objects.create(
                title="New Teacher Registration",
                message=f"A new teacher account '{username}' ({full_name}) is pending approval.",
                icon="User",
                link_url="/dashboard/#section-users"
            )
            
            messages.success(request, 'Registration successful! Please wait for the Main Admin to approve your account.')
            return redirect('login')
    return render(request, 'main/teacher_register.html')

def logout_view(request):
    if request.user.is_authenticated:
        log_audit_event(request, 'logout', request.user, {'source': 'auth'}, target_label=request.user.username)
    logout(request)
    return redirect('home')


# Dashboard

# Dashboard

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def dashboard(request):
    user_role = request.user.profile.role
    
    if user_role == 'SUPER_ADMIN':
        context = {
            'role': 'SUPER_ADMIN',
            'role_display': 'Main Admin',
            'total_videos':     AnimationVideo.objects.filter(is_archived=False).count(),
            'total_flipbooks':  Flipbook.objects.filter(is_archived=False).count(),
            'total_users':      User.objects.count(),
            'total_categories': Category.objects.count(),
            'pending_teachers': User.objects.filter(profile__role='TEACHER', profile__is_approved=False),
            'pending_videos':   AnimationVideo.objects.filter(is_approved=False, is_archived=False),
            'pending_flipbooks': Flipbook.objects.filter(is_approved=False, is_archived=False),
            'recent_audit_logs': AuditLog.objects.select_related('actor')[:8],
            'all_videos':       AnimationVideo.objects.filter(is_archived=False).order_by('-created_at'),
            'all_flipbooks':    Flipbook.objects.filter(is_archived=False).order_by('-created_at'),
            'archived_videos':  AnimationVideo.objects.filter(is_archived=True).order_by('-created_at'),
            'archived_flipbooks': Flipbook.objects.filter(is_archived=True).order_by('-created_at'),
            'users':            User.objects.order_by('-date_joined'),
            'categories':       Category.objects.all(),
            'announcements':    Announcement.objects.all().order_by('-created_at'),
        }
    else: # TEACHER
        context = {
            'role': 'TEACHER',
            'role_display': 'Teacher',
            'my_videos':    AnimationVideo.objects.filter(author=request.user, is_archived=False),
            'my_flipbooks': Flipbook.objects.filter(author=request.user, is_archived=False),
            'categories':   Category.objects.all(),
        }
        
    return render(request, 'main/dashboard.html', context)

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def approve_content(request, model_type, pk):
    if model_type == 'video':
        AnimationVideo.objects.filter(pk=pk).update(is_approved=True)
        obj = AnimationVideo.objects.get(pk=pk)
    elif model_type == 'flipbook':
        Flipbook.objects.filter(pk=pk).update(is_approved=True)
        obj = Flipbook.objects.get(pk=pk)
    else:
        return redirect('dashboard')
        
    log_audit_event(request, 'approve', obj, {'source': 'dashboard'})
    messages.success(request, f'{model_type.capitalize()} approved!')
    return redirect('dashboard')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def approve_teacher(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Update profile attribute
    if hasattr(user, 'profile'):
        user.profile.is_approved = True
        user.profile.save()
    
    # Update user staff status
    user.is_staff = True
    user.save()
    
    log_audit_event(request, 'approve', user, {'source': 'dashboard'}, target_label=user.username)
    
    messages.success(request, f'Teacher {user.username} approved!')
    return redirect('dashboard')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def toggle_user_status(request, pk):
    if request.user.pk == pk:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    action = 'restore' if user.is_active else 'archive'
    log_audit_event(request, action, user, {'source': 'dashboard'}, target_label=user.username)
    status_str = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.username} has been {status_str}.')
    return redirect('dashboard')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def delete_user(request, pk):
    if request.method == 'POST':
        if request.user.pk == pk:
            messages.error(request, "You cannot delete your own account.")
            return redirect('dashboard')
            
        user = get_object_or_404(User, pk=pk)
        username = user.username
        log_audit_event(request, 'delete', user, {'source': 'dashboard'}, target_label=username)
        user.delete()
        
        messages.success(request, f'User {username} deleted successfully.')
    return redirect('dashboard')


# Category CRUD

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
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
@user_passes_test(is_super_admin, login_url='home')
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
@user_passes_test(is_super_admin, login_url='home')
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
@user_passes_test(is_super_admin, login_url='home')
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
@user_passes_test(is_super_admin, login_url='home')
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
@user_passes_test(is_super_admin, login_url='home')
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        log_audit_event(request, 'delete', announcement, {'source': 'dashboard'})
        announcement.delete()
        messages.success(request, 'Announcement deleted!')
        return redirect('dashboard')
    return render(request, 'main/confirm_delete.html', {'object': announcement})