from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from .audit import log_audit_event
from .models import AnimationVideo, AuditLog, Flipbook, Category, Announcement, Notification, VideoComment, FlipbookComment, UserProfile, StudentActivity, CalendarEvent, TeacherTask, PasswordResetCode
from .forms import AnimationVideoForm, FlipbookForm, AnnouncementForm, UserUpdateForm, UserProfileUpdateForm, CalendarEventForm

import urllib.request
import urllib.parse
import json
from django.conf import settings
import re

def verify_recaptcha(request):
    recaptcha_response = request.POST.get('g-recaptcha-response')
    if not recaptcha_response:
        return False
        
    data = urllib.parse.urlencode({
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }).encode('utf-8')
    
    req = urllib.request.Request('https://www.google.com/recaptcha/api/siteverify', data=data)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('success', False)
    except Exception:
        return False

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
        if 'remove_pfp' in request.POST:
            request.user.profile.profile_picture.delete(save=True)
            messages.success(request, 'Profile picture removed successfully!')
            return redirect('profile')
            
        old_grade = request.user.profile.grade_level
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            new_grade = p_form.cleaned_data.get('grade_level')
            if new_grade != old_grade and request.user.profile.role == 'CLIENT':
                from django.utils import timezone
                from datetime import timedelta
                
                # Check cooldown before saving anything
                if request.user.profile.grade_change_cooldown:
                    if timezone.now() < request.user.profile.grade_change_cooldown + timedelta(minutes=2):
                        messages.error(request, 'You recently cancelled a grade change request. Please wait a few minutes before trying again.')
                        return redirect('profile')
                
                # Revert the in-memory grade level so the User save signal doesn't save the new grade incorrectly
                request.user.profile.grade_level = old_grade

            u_form.save()
            profile = p_form.save(commit=False)
            
            if new_grade != old_grade and request.user.profile.role == 'CLIENT':
                profile.grade_level = old_grade
                profile.pending_grade = new_grade
                messages.success(request, 'Your profile has been updated. Grade change request submitted to Admin.')
            else:
                messages.success(request, 'Your profile has been updated successfully!')
                
            profile.save()
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

@login_required(login_url='login')
def cancel_grade_request(request):
    if request.method == 'POST':
        from django.utils import timezone
        profile = request.user.profile
        if profile.pending_grade:
            profile.pending_grade = None
            profile.grade_change_cooldown = timezone.now()
            profile.save()
            messages.success(request, 'Grade change request cancelled. You must wait 2 minutes before requesting again.')
    return redirect('profile')

@login_required
def verify_password_ajax(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            password = data.get('password', '')
            user = authenticate(username=request.user.username, password=password)
            if user is not None:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Incorrect password.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})

@login_required
def update_password_ajax(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            new_password = data.get('new_password', '')
            confirm_password = data.get('confirm_password', '')
            
            if len(new_password) < 8:
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long.'})
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'Passwords do not match.'})
                
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user) # Keep user logged in
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})

def faqs(request):
    return render(request, 'main/faqs.html')

from django.utils.timezone import now

def notifications(request):
    qs = Notification.objects.all()
    
    # Filter admin-only notifications for regular users
    if not is_super_admin(request.user):
        qs = qs.exclude(title__icontains='Pending').exclude(title__icontains='Registration')
        
    notifications_list = qs
    
    # Update profile to hide the indicator
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        request.user.profile.last_seen_notifications = now()
        request.user.profile.save()
    
    return render(request, 'main/notifications.html', {'notifications': notifications_list})


# Animation Videos CRUD

def video_list(request):
    category = request.GET.get('category')
    craft_category = request.GET.get('craft_category', 'All Categories')
    query = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', 'All Grades')
    
    videos = AnimationVideo.objects.filter(is_archived=False, is_approved=True)
    
    is_client = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'CLIENT'
    
    if is_client:
        user_grade = request.user.profile.grade_level
        if user_grade:
            from django.db.models import Q
            videos = videos.filter(Q(grade=user_grade) | Q(grade='All Grades'))
            grade = user_grade
    else:
        if grade and grade != 'All Grades':
            videos = videos.filter(grade=grade)
            
    if category:
        videos = videos.filter(category__name=category)
    
    if craft_category and craft_category != 'All Categories':
        videos = videos.filter(craft_category=craft_category)
    
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
        return redirect('/dashboard/#section-videos' if request.user.is_staff else 'video_list')
    return render(request, 'main/video_form.html', {'form': form, 'title': 'Add Video'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def video_edit(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    form = AnimationVideoForm(request.POST or None, request.FILES or None, instance=video)
    if form.is_valid():
        updated_video = form.save()
        log_audit_event(request, 'update', updated_video, {'source': 'dashboard'})
        return redirect('/dashboard/#section-videos' if request.user.is_staff else 'video_list')
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
        return redirect('/dashboard/#section-videos' if request.user.is_staff else 'video_list')
    return render(request, 'main/confirm_delete.html', {'object': video})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def video_restore(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    if request.user.profile.role != 'SUPER_ADMIN' and video.author != request.user:
        messages.error(request, 'You do not have permission to do this.')
        return redirect('/dashboard/#section-archive')
    video.is_archived = False
    video.save()
    log_audit_event(request, 'restore', video, {'source': 'dashboard'})
    messages.success(request, 'Video restored successfully!')
    return redirect('/dashboard/#section-archive')
    
@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def video_permanent_delete(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk)
    if request.user.profile.role != 'SUPER_ADMIN' and video.author != request.user:
        messages.error(request, 'You do not have permission to do this.')
        return redirect('/dashboard/#section-archive')
    if request.method == 'POST':
        log_audit_event(request, 'delete', video, {'source': 'dashboard'})
        video.delete()
        messages.success(request, 'Video permanently deleted!')
        return redirect('/dashboard/#section-archive')
    return render(request, 'main/confirm_delete.html', {'object': video, 'permanent': True})

@login_required(login_url='login')
def video_detail(request, pk):
    video = get_object_or_404(AnimationVideo, pk=pk, is_archived=False)
    comments = video.comments.filter(is_archived=False)
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
            VideoComment.objects.create(video=video, user=request.user, name=name, text=text)
    return redirect('video_detail', pk=pk)

@login_required(login_url='login')
def video_comment_delete(request, pk):
    comment = get_object_or_404(VideoComment, pk=pk)
    if request.user == comment.user or (hasattr(request.user, 'profile') and request.user.profile.role == 'SUPER_ADMIN'):
        comment.is_archived = True
        comment.save()
        messages.success(request, 'Comment deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this comment.')
    return redirect('video_detail', pk=comment.video.pk)


# Flipbooks CRUD

def flipbook_list(request):
    category = request.GET.get('category')
    craft_category = request.GET.get('craft_category', 'All Categories')
    query = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', 'All Grades')
    
    flipbooks = Flipbook.objects.filter(is_archived=False, is_approved=True)
    
    is_client = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'CLIENT'
    
    if is_client:
        user_grade = request.user.profile.grade_level
        if user_grade:
            from django.db.models import Q
            flipbooks = flipbooks.filter(Q(grade=user_grade) | Q(grade='All Grades'))
            grade = user_grade
    else:
        if grade and grade != 'All Grades':
            flipbooks = flipbooks.filter(grade=grade)
            
    if category:
        flipbooks = flipbooks.filter(category__name=category)
    
    if craft_category and craft_category != 'All Categories':
        flipbooks = flipbooks.filter(craft_category=craft_category)
    
    if query:
        flipbooks = flipbooks.filter(title__icontains=query)
        
    return render(request, 'main/flipbook_list.html', {'flipbooks': flipbooks, 'active': category, 'selected_grade': grade, 'selected_craft': craft_category})

# DITO KO IDINAGDAG YUNG FLIPBOOK DETAIL VIEW
@login_required(login_url='login')
def flipbook_detail(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk, is_archived=False)
    comments = flipbook.comments.filter(is_archived=False)
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
            FlipbookComment.objects.create(flipbook=flipbook, user=request.user, name=name, text=text)
    return redirect('flipbook_detail', pk=pk)

@login_required(login_url='login')
def flipbook_comment_delete(request, pk):
    comment = get_object_or_404(FlipbookComment, pk=pk)
    if request.user == comment.user or (hasattr(request.user, 'profile') and request.user.profile.role == 'SUPER_ADMIN'):
        comment.is_archived = True
        comment.save()
        messages.success(request, 'Comment deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this comment.')
    return redirect('flipbook_detail', pk=comment.flipbook.pk)

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
        return redirect('/dashboard/#section-flipbooks' if request.user.is_staff else 'flipbook_list')
    return render(request, 'main/flipbook_form.html', {'form': form, 'title': 'Add Flipbook'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def flipbook_edit(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    form = FlipbookForm(request.POST or None, request.FILES or None, instance=flipbook)
    if form.is_valid():
        updated_flipbook = form.save()
        log_audit_event(request, 'update', updated_flipbook, {'source': 'dashboard'})
        return redirect('/dashboard/#section-flipbooks' if request.user.is_staff else 'flipbook_list')
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
        return redirect('/dashboard/#section-flipbooks' if request.user.is_staff else 'flipbook_list')
    return render(request, 'main/confirm_delete.html', {'object': flipbook})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def flipbook_restore(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    if request.user.profile.role != 'SUPER_ADMIN' and flipbook.author != request.user:
        messages.error(request, 'You do not have permission to do this.')
        return redirect('/dashboard/#section-archive')
    flipbook.is_archived = False
    flipbook.save()
    log_audit_event(request, 'restore', flipbook, {'source': 'dashboard'})
    messages.success(request, 'Flipbook restored successfully!')
    return redirect('/dashboard/#section-archive')

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def flipbook_permanent_delete(request, pk):
    flipbook = get_object_or_404(Flipbook, pk=pk)
    if request.user.profile.role != 'SUPER_ADMIN' and flipbook.author != request.user:
        messages.error(request, 'You do not have permission to do this.')
        return redirect('/dashboard/#section-archive')
    if request.method == 'POST':
        log_audit_event(request, 'delete', flipbook, {'source': 'dashboard'})
        flipbook.delete()
        messages.success(request, 'Flipbook permanently deleted!')
        return redirect('/dashboard/#section-archive')
    return render(request, 'main/confirm_delete.html', {'object': flipbook, 'permanent': True})

# Auth

def login_view(request, template_name='main/login.html'):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        if not verify_recaptcha(request):
            messages.error(request, 'CAPTCHA verification failed. Please try again.')
            return render(request, template_name, {'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})
            
        user = authenticate(request, username=username, password=password)
        if user:
            if template_name == 'main/teacher_login.html' and user.profile.role not in ['TEACHER', 'SUPER_ADMIN']:
                messages.error(request, 'Student accounts cannot log in through the Teacher portal.')
                return render(request, template_name)
            elif template_name == 'main/login.html' and user.profile.role != 'CLIENT':
                messages.error(request, 'Teacher and Admin accounts must log in through the Teacher portal.')
                return render(request, template_name)

            if not user.profile.is_approved and user.profile.role != 'SUPER_ADMIN':
                messages.error(request, 'Your account is pending approval from the Main Admin.')
                return render(request, template_name)
            
            login(request, user)
            log_audit_event(request, 'login', user, {'source': 'auth'}, target_label=user.username)
            
            if next_url:
                return redirect(next_url)
                
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, template_name, {'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        lrn_number = request.POST.get('lrn_number')
        grade_level = request.POST.get('grade_level')
        section    = request.POST.get('section')
        username   = request.POST.get('username')
        password1  = request.POST.get('password1')
        password2  = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif not re.search(r'[a-zA-Z]', password1) or not re.search(r'[0-9]', password1) or not re.search(r'_', password1):
            messages.error(request, 'Password must contain a combination of letters, numbers, and an underscore.')
        elif not email or not email.lower().endswith('@gmail.com'):
            pass # Frontend will handle the warning display
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'This Gmail account is already registered. Please use a different one.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif not lrn_number or not lrn_number.isdigit() or len(lrn_number) != 12:
            messages.error(request, 'LRN Number must be exactly 12 digits.')
        elif UserProfile.objects.filter(lrn_number=lrn_number).exists():
            messages.error(request, 'This LRN Number is already registered by another user. Please use a different one.')
        elif not section or not re.match(r'^[1-3]$', section):
            messages.error(request, 'Section must be a single number from 1 to 3.')
        elif not verify_recaptcha(request):
            messages.error(request, 'CAPTCHA verification failed. Please prove you are human.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Profile is automatically created by signal, just update it
            user.profile.lrn_number = lrn_number
            if grade_level:
                user.profile.grade_level = grade_level
            if section:
                # Combine grade level number with section number (e.g. "Grade 1" & "3" -> "1-3")
                grade_match = re.search(r'\d+', grade_level) if grade_level else None
                grade_num = grade_match.group() if grade_match else '1'
                user.profile.section = f"{grade_num}-{section}"
            user.profile.save()
            
            # Profile defaults to CLIENT, which is correct here
            # Set is_approved to False explicitly (although default is False)
            user.profile.is_approved = False
            user.profile.save()
            
            log_audit_event(request, 'register', user, {'source': 'auth'}, target_label=user.username)
            
            # Notify Super Admin
            full_name_combined = f"{first_name} {last_name}".strip()
            from main.models import Notification
            Notification.objects.create(
                title="New Student Registration",
                message=f"A new student account '{username}' ({full_name_combined}) is pending approval.",
                icon="User",
                link_url="/dashboard/#section-pending"
            )
            
            # Send Email Notification to Student
            subject = "Registration Submitted - CraftyKids"
            website_link = request.build_absolute_uri('/')
            message_body = (
                f"Hello {first_name} {last_name},\n\n"
                f"Thank you for registering on CraftyKids!\n\n"
                f"We have successfully received your student registration request. "
                f"Please note that all new accounts require approval by the Main Admin "
                f"before you can log in. We will send you an email once your account has been reviewed.\n\n"
                f"You can visit our website here: {website_link}\n\n"
                f"Thank you,\n"
                f"CraftyKids Team"
            )
            try:
                send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [email])
            except Exception as e:
                print(f"Failed to send student registration email: {e}")
            
            messages.success(request, 'Registration successful! Please wait for the Main Admin to approve your account. We will send you an email if your account was approved, or denied.')
            return redirect('login')
            
    return render(request, 'main/register.html', {
        'form_data': request.POST if request.method == 'POST' else None,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY
    })

def teacher_register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        username   = request.POST.get('username')
        password1  = request.POST.get('password1')
        password2  = request.POST.get('password2')
        grade_level = request.POST.get('grade_level')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif not re.search(r'[a-zA-Z]', password1) or not re.search(r'[0-9]', password1) or not re.search(r'_', password1):
            messages.error(request, 'Password must contain a combination of letters, numbers, and an underscore.')
        elif not email or not email.lower().endswith('@gmail.com'):
            pass # Frontend will handle the warning display
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'This Gmail account is already registered. Please use a different one.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif not verify_recaptcha(request):
            messages.error(request, 'CAPTCHA verification failed. Please prove you are human.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Set role to TEACHER and is_approved to False
            user.profile.role = 'TEACHER'
            user.profile.is_approved = False
            
            if grade_level:
                user.profile.grade_level = grade_level
            
            faculty_id = request.FILES.get('faculty_id')
            if faculty_id:
                user.profile.faculty_id_image = faculty_id
                
            user.profile.save()
            
            log_audit_event(request, 'register', user, {'source': 'teacher_auth'}, target_label=user.username)
            
            # Notify Super Admin
            full_name_combined = f"{first_name} {last_name}".strip()
            Notification.objects.create(
                title="New Teacher Registration",
                message=f"A new teacher account '{username}' ({full_name_combined}) is pending approval.",
                icon="User",
                link_url="/dashboard/#section-users"
            )
            
            # Send Email Notification to Teacher
            subject = "Registration Submitted - CraftyKids"
            website_link = request.build_absolute_uri('/')
            message_body = (
                f"Hello {first_name} {last_name},\n\n"
                f"Thank you for registering on CraftyKids!\n\n"
                f"We have successfully received your teacher registration request. "
                f"Please note that all new teacher accounts require approval by the Main Admin "
                f"before you can log in. We will send you an email once your account has been reviewed.\n\n"
                f"You can visit our website here: {website_link}\n\n"
                f"Thank you,\n"
                f"CraftyKids Team"
            )
            try:
                send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [email])
            except Exception as e:
                print(f"Failed to send teacher registration email: {e}")
            
            messages.success(request, 'Registration successful! Please wait for the Main Admin to approve your account. We will send you an email if your account was approved, or denied.')
            return redirect('login')
            
    return render(request, 'main/teacher_register.html', {
        'form_data': request.POST if request.method == 'POST' else None,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY
    })

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
            'pending_users':    User.objects.filter(profile__is_approved=False, is_active=True).exclude(profile__role='SUPER_ADMIN'),
            'pending_grade_users': User.objects.filter(profile__pending_grade__isnull=False).exclude(profile__pending_grade=''),
            'pending_videos':   AnimationVideo.objects.filter(is_approved=False, is_archived=False),
            'pending_flipbooks': Flipbook.objects.filter(is_approved=False, is_archived=False),
            'recent_audit_logs': AuditLog.objects.select_related('actor')[:8],
            'all_videos':       AnimationVideo.objects.filter(is_archived=False).order_by('-created_at'),
            'all_flipbooks':    Flipbook.objects.filter(is_archived=False).order_by('-created_at'),
            'archived_videos':  AnimationVideo.objects.filter(is_archived=True).order_by('-created_at'),
            'archived_flipbooks': Flipbook.objects.filter(is_archived=True).order_by('-created_at'),
            'archived_video_comments': VideoComment.objects.filter(is_archived=True).order_by('-created_at'),
            'archived_flipbook_comments': FlipbookComment.objects.filter(is_archived=True).order_by('-created_at'),
            'users':            User.objects.filter(profile__is_archived=False).order_by('-date_joined'),
            'archived_users':   User.objects.filter(profile__is_archived=True).order_by('-date_joined'),
            'categories':       Category.objects.all(),
            'announcements':    Announcement.objects.filter(is_archived=False).order_by('-created_at'),
            'archived_announcements': Announcement.objects.filter(is_archived=True).order_by('-created_at'),
            'calendar_events':  CalendarEvent.objects.filter(is_archived=False).order_by('date'),
            'archived_events':  CalendarEvent.objects.filter(is_archived=True).order_by('date'),
        }

        # Pre-group pending items by dynamic student sections/grades for vertical Kanban columns
        pending_users_by_grade = {}
        for u in context['pending_users']:
            if u.profile.role == 'TEACHER':
                if u.profile.grade_level:
                    group_name = f"Teacher {u.profile.grade_level}"
                else:
                    group_name = 'Teachers'
            elif u.profile.section:
                group_name = u.profile.section
            elif u.profile.grade_level:
                group_name = u.profile.grade_level
            else:
                group_name = 'Others'
                
            if group_name not in pending_users_by_grade:
                pending_users_by_grade[group_name] = []
            pending_users_by_grade[group_name].append(u)
            
        def get_group_sort_key(group_name):
            if group_name == 'Teachers':
                return (999, 'Teachers')
            if group_name.startswith('Teacher Grade'):
                import re
                match = re.search(r'\d+', group_name)
                num = int(match.group()) if match else 0
                return (100 + num, group_name)
            import re
            match = re.search(r'\d+', group_name)
            if match:
                num = int(match.group())
                return (num, group_name)
            return (500, group_name)
            
        pending_users_by_grade = dict(sorted(pending_users_by_grade.items(), key=lambda x: get_group_sort_key(x[0])))

        pending_grade_users_by_grade = {
            'Grade 1': [],
            'Grade 2': [],
            'Grade 3': [],
            'Grade 4': [],
            'Grade 5': [],
            'Grade 6': [],
        }
        for u in context['pending_grade_users']:
            p_grade = u.profile.pending_grade
            if p_grade in pending_grade_users_by_grade:
                pending_grade_users_by_grade[p_grade].append(u)
            else:
                if 'Others' not in pending_grade_users_by_grade:
                    pending_grade_users_by_grade['Others'] = []
                pending_grade_users_by_grade['Others'].append(u)

        pending_videos_by_grade = {
            'Grade 1': [],
            'Grade 2': [],
            'Grade 3': [],
            'Grade 4': [],
            'Grade 5': [],
            'Grade 6': [],
        }
        for v in context['pending_videos']:
            v_grade = v.grade
            if v_grade in pending_videos_by_grade:
                pending_videos_by_grade[v_grade].append(v)
            else:
                if 'All Grades & Others' not in pending_videos_by_grade:
                    pending_videos_by_grade['All Grades & Others'] = []
                pending_videos_by_grade['All Grades & Others'].append(v)

        pending_flipbooks_by_grade = {
            'Grade 1': [],
            'Grade 2': [],
            'Grade 3': [],
            'Grade 4': [],
            'Grade 5': [],
            'Grade 6': [],
        }
        for f in context['pending_flipbooks']:
            f_grade = f.grade
            if f_grade in pending_flipbooks_by_grade:
                pending_flipbooks_by_grade[f_grade].append(f)
            else:
                if 'All Grades & Others' not in pending_flipbooks_by_grade:
                    pending_flipbooks_by_grade['All Grades & Others'] = []
                pending_flipbooks_by_grade['All Grades & Others'].append(f)

        # Group announcements by grade
        announcements_by_grade = {
            'All Grades': [],
            'Grade 1': [],
            'Grade 2': [],
            'Grade 3': [],
            'Grade 4': [],
            'Grade 5': [],
            'Grade 6': [],
        }
        for ann in context['announcements']:
            a_grade = ann.grade
            if a_grade in announcements_by_grade:
                announcements_by_grade[a_grade].append(ann)
            else:
                announcements_by_grade['All Grades'].append(ann)

        context.update({
            'pending_users_by_grade': pending_users_by_grade,
            'pending_grade_users_by_grade': pending_grade_users_by_grade,
            'pending_videos_by_grade': pending_videos_by_grade,
            'pending_flipbooks_by_grade': pending_flipbooks_by_grade,
            'announcements_by_grade': announcements_by_grade,
        })
    else: # TEACHER
        context = {
            'role': 'TEACHER',
            'role_display': 'Teacher',
            'my_videos':    AnimationVideo.objects.filter(author=request.user, is_archived=False),
            'my_flipbooks': Flipbook.objects.filter(author=request.user, is_archived=False),
            'archived_videos': AnimationVideo.objects.filter(author=request.user, is_archived=True).order_by('-created_at'),
            'archived_flipbooks': Flipbook.objects.filter(author=request.user, is_archived=True).order_by('-created_at'),
            'archived_video_comments': VideoComment.objects.filter(video__author=request.user, is_archived=True).order_by('-created_at'),
            'archived_flipbook_comments': FlipbookComment.objects.filter(flipbook__author=request.user, is_archived=True).order_by('-created_at'),
            'categories':   Category.objects.all(),
            'calendar_events': CalendarEvent.objects.filter(is_archived=False).order_by('date'),
            'archived_events': CalendarEvent.objects.filter(is_archived=True).order_by('date'),
        }
        
    context['teacher_tasks'] = TeacherTask.objects.filter(user=request.user).order_by('created_at')
    
    # Add JSON events for the calendar javascript
    events_list = []
    for evt in context['calendar_events']:
        events_list.append({
            'title': evt.title,
            'date': evt.date.isoformat(),
            'type': evt.event_type,
            'description': evt.description,
            'image_url': evt.image.url if evt.image else ''
        })
        
    for task in context['teacher_tasks']:
        if task.due_date:
            events_list.append({
                'title': f"[Task] {task.title}",
                'date': task.due_date.isoformat(),
                'type': 'task',
                'description': f"Status: {task.status}",
                'image_url': ''
            })
            
    context['events_json'] = json.dumps(events_list)
        
    return render(request, 'main/dashboard.html', context)

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def approve_content(request, model_type, pk):
    if model_type == 'video':
        obj = get_object_or_404(AnimationVideo, pk=pk)
    elif model_type == 'flipbook':
        obj = get_object_or_404(Flipbook, pk=pk)
    else:
        return redirect('/dashboard/#section-pending')
        
    if request.method == 'POST':
        if model_type == 'video':
            AnimationVideo.objects.filter(pk=pk).update(is_approved=True)
        elif model_type == 'flipbook':
            Flipbook.objects.filter(pk=pk).update(is_approved=True)
            
        log_audit_event(request, 'approve', obj, {'source': 'dashboard'})
        messages.success(request, f'{model_type.capitalize()} approved!')
        return redirect('/dashboard/#section-pending')
        
    return render(request, 'main/confirm_action.html', {
        'title': f'Approve {model_type.capitalize()}?',
        'icon': '✅',
        'message': f'You are about to approve the {model_type} "<strong>{obj.title}</strong>". It will be visible to all users.',
        'btn_text': 'Yes, Approve!',
        'is_destructive': False
    })

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def approve_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    role_display = user.profile.get_role_display() if hasattr(user, 'profile') else 'User'
    
    if request.method == 'POST':
        # Update profile attribute
        if hasattr(user, 'profile'):
            user.profile.is_approved = True
            user.profile.save()
        
        # Update user staff status if teacher
        if hasattr(user, 'profile') and user.profile.role == 'TEACHER':
            user.is_staff = True
        user.save()
        
        # Send Email Notification to the Approved User
        if user.email:
            subject = "Account Approved - CraftyKids"
            login_link = request.build_absolute_uri(reverse('login'))
            message_body = (
                f"Hello {user.first_name or user.username},\n\n"
                f"Great news! Your account on CraftyKids has been approved by the Main Admin.\n\n"
                f"You can now log in to your account and explore all our features:\n"
                f"{login_link}\n\n"
                f"Thank you,\n"
                f"CraftyKids Team"
            )
            try:
                send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [user.email])
            except Exception as e:
                print(f"Failed to send approval email: {e}")
        
        log_audit_event(request, 'approve', user, {'source': 'dashboard'}, target_label=user.username)
        messages.success(request, f'{role_display} {user.username} approved!')
        return redirect('/dashboard/#section-pending')
        
    return render(request, 'main/confirm_action.html', {
        'title': 'Approve Account?',
        'icon': '✅',
        'message': f'You are about to approve the {role_display} account for "<strong>{user.username}</strong>".',
        'btn_text': 'Yes, Approve!',
        'is_destructive': False
    })

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def approve_grade(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if hasattr(user, 'profile') and user.profile.pending_grade:
            user.profile.grade_level = user.profile.pending_grade
            user.profile.pending_grade = None
            user.profile.save()
            log_audit_event(request, 'approve_grade', user, {'source': 'dashboard'}, target_label=user.username)
            messages.success(request, f'Grade level updated for {user.username}!')
        return redirect('/dashboard/#section-pending')
    
    return render(request, 'main/confirm_action.html', {
        'title': 'Approve Grade Change?',
        'icon': '✅',
        'message': f'Approve grade change to <strong>{user.profile.pending_grade}</strong> for "<strong>{user.username}</strong>"?',
        'btn_text': 'Yes, Approve!',
        'is_destructive': False
    })

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def reject_grade(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if hasattr(user, 'profile'):
            user.profile.pending_grade = None
            user.profile.save()
            log_audit_event(request, 'reject_grade', user, {'source': 'dashboard'}, target_label=user.username)
            messages.success(request, f'Grade change rejected for {user.username}.')
        return redirect('/dashboard/#section-pending')
        
    return render(request, 'main/confirm_action.html', {
        'title': 'Reject Grade Change?',
        'icon': '🚫',
        'message': f'Reject grade change request for "<strong>{user.username}</strong>"?',
        'btn_text': 'Yes, Reject!',
        'is_destructive': True
    })

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def reject_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    username = user.username
    role_display = user.profile.get_role_display() if hasattr(user, 'profile') else 'User'
    
    if request.method == 'POST':
        if hasattr(user, 'profile'):
            user.profile.is_archived = True
            user.profile.save()
        user.is_active = False
        user.save()
        
        log_audit_event(request, 'archive', user, {'source': 'dashboard'}, target_label=username)
        messages.success(request, f'{role_display} {username} request denied and account archived.')
        return redirect('/dashboard/#section-pending')
        
    return render(request, 'main/confirm_action.html', {
        'title': 'Deny Account?',
        'icon': '🚫',
        'message': f'You are about to deny the {role_display} account for "<strong>{username}</strong>". It will be archived and hidden from users.',
        'btn_text': 'Yes, Deny!',
        'is_destructive': True
    })


@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def toggle_user_status(request, pk):
    if request.user.pk == pk:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('/dashboard/#section-users')
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    action = 'restore' if user.is_active else 'archive'
    log_audit_event(request, action, user, {'source': 'dashboard'}, target_label=user.username)
    status_str = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.username} has been {status_str}.')
    return redirect('/dashboard/#section-users')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def delete_user(request, pk):
    if request.method == 'POST':
        if request.user.pk == pk:
            messages.error(request, "You cannot archive your own account.")
            return redirect('/dashboard/#section-users')
            
        user = get_object_or_404(User, pk=pk)
        username = user.username
        
        if hasattr(user, 'profile'):
            user.profile.is_archived = True
            user.profile.save()
        user.is_active = False
        user.save()
        
        log_audit_event(request, 'archive', user, {'source': 'dashboard'}, target_label=username)
        messages.success(request, f'User {username} archived successfully.')
    return redirect('/dashboard/#section-users')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def user_restore(request, pk):
    user = get_object_or_404(User, pk=pk)
    if hasattr(user, 'profile'):
        user.profile.is_archived = False
        user.profile.save()
    user.is_active = True
    user.save()
    
    log_audit_event(request, 'restore', user, {'source': 'dashboard'}, target_label=user.username)
    messages.success(request, f'User {user.username} restored successfully!')
    return redirect('/dashboard/#section-archive')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def user_permanent_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if request.user.pk == pk:
            messages.error(request, "You cannot delete your own account.")
            return redirect('/dashboard/#section-archive')
        username = user.username
        log_audit_event(request, 'delete', user, {'source': 'dashboard'}, target_label=username)
        user.delete()
        messages.success(request, f'User {username} permanently deleted!')
        return redirect('/dashboard/#section-archive')
    return render(request, 'main/confirm_delete.html', {'object': user, 'permanent': True})

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
        return redirect('/dashboard/#section-archive')
    return redirect('/dashboard/#section-archive')

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
    announcements = Announcement.objects.filter(is_active=True, is_archived=False)
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.role == 'CLIENT':
            from django.db.models import Q
            grade_filter = Q(grade='All Grades')
            if profile.grade_level:
                grade_filter |= Q(grade=profile.grade_level)
            announcements = announcements.filter(target_audience='Student').filter(grade_filter)
    else:
        announcements = announcements.filter(target_audience='Student', grade='All Grades')
        
    announcements = announcements.order_by('-created_at')
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
        return redirect('/dashboard/#section-announcements')
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
        return redirect('/dashboard/#section-announcements')
    return render(request, 'main/announcement_form.html', {'form': form, 'title': 'Edit Announcement'})


@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.is_archived = True
        announcement.save()
        log_audit_event(request, 'archive', announcement, {'source': 'dashboard'})
        messages.success(request, 'Announcement archived!')
        return redirect('/dashboard/#section-announcements')
    return render(request, 'main/confirm_delete.html', {'object': announcement})

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def announcement_restore(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_archived = False
    announcement.save()
    log_audit_event(request, 'restore', announcement, {'source': 'dashboard'})
    messages.success(request, 'Announcement restored!')
    return redirect('/dashboard/#section-archive')

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def announcement_permanent_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        log_audit_event(request, 'delete', announcement, {'source': 'dashboard'})
        announcement.delete()
        messages.success(request, 'Announcement permanently deleted!')
        return redirect('/dashboard/#section-archive')
    return render(request, 'main/confirm_delete.html', {'object': announcement, 'permanent': True})

# Calendar Activities

@login_required(login_url='login')
def student_calendar(request):
    import json
    from django.utils.timezone import now
    from datetime import timedelta
    
    # Get all activities for the student
    activities = StudentActivity.objects.filter(user=request.user)
    
    # Generate weekly wrap-up statistics
    today = now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    week_activities = activities.filter(completed_at__date__gte=start_of_week)
    total_week_crafts = week_activities.count()
    videos_completed = week_activities.filter(video__isnull=False).count()
    flipbooks_completed = week_activities.filter(flipbook__isnull=False).count()
    
    # Prepare data for the frontend calendar
    events = []
    for act in activities:
        title = act.video.title if act.video else act.flipbook.title if act.flipbook else "Activity"
        events.append({
            'title': title,
            'start': act.completed_at.strftime('%Y-%m-%d'),
            'type': 'video' if act.video else 'flipbook'
        })
        
    calendar_events = CalendarEvent.objects.filter(is_archived=False)
    for evt in calendar_events:
        events.append({
            'title': evt.title,
            'start': evt.date.strftime('%Y-%m-%d'),
            'type': 'holiday' if evt.event_type == 'Holiday' else 'event',
        })
        
    context = {
        'events_json': json.dumps(events),
        'total_week_crafts': total_week_crafts,
        'videos_completed': videos_completed,
        'flipbooks_completed': flipbooks_completed,
    }
    
    return render(request, 'main/calendar.html', context)

import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@login_required
@require_POST
def mark_completed(request):
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        flipbook_id = data.get('flipbook_id')
        
        if video_id:
            video = get_object_or_404(AnimationVideo, pk=video_id)
            # Avoid duplicate completion on the same day if desired, but for now just record it
            StudentActivity.objects.create(user=request.user, video=video)
            return JsonResponse({'status': 'success', 'message': 'Video completion recorded!'})
            
        if flipbook_id:
            flipbook = get_object_or_404(Flipbook, pk=flipbook_id)
            StudentActivity.objects.create(user=request.user, flipbook=flipbook)
            return JsonResponse({'status': 'success', 'message': 'Flipbook completion recorded!'})
            
        return JsonResponse({'status': 'error', 'message': 'No valid ID provided.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Calendar Events CRUD

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def calendar_event_create(request):
    form = CalendarEventForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        event = form.save(commit=False)
        event.author = request.user
        event.save()
        log_audit_event(request, 'create', event, {'source': 'dashboard', 'status': 'approved'})
        messages.success(request, 'Calendar Event/Holiday added successfully!')
        return redirect('/dashboard/#section-calendar')
    return render(request, 'main/calendar_event_form.html', {'form': form, 'title': 'Add Calendar Event'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def calendar_event_edit(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    form = CalendarEventForm(request.POST or None, request.FILES or None, instance=event)
    if form.is_valid():
        updated_event = form.save()
        log_audit_event(request, 'update', updated_event, {'source': 'dashboard'})
        messages.success(request, 'Calendar Event/Holiday updated successfully!')
        return redirect('/dashboard/#section-calendar')
    return render(request, 'main/calendar_event_form.html', {'form': form, 'title': 'Edit Calendar Event'})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def calendar_event_delete(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    if request.method == 'POST':
        event.is_archived = True
        event.save()
        log_audit_event(request, 'archive', event, {'source': 'dashboard'})
        messages.success(request, 'Calendar Event/Holiday archived successfully!')
        return redirect('/dashboard/#section-calendar')
    return render(request, 'main/confirm_delete.html', {'object': event})

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def calendar_event_restore(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    event.is_archived = False
    event.save()
    log_audit_event(request, 'restore', event, {'source': 'dashboard'})
    messages.success(request, 'Calendar Event restored successfully!')
    return redirect('/dashboard/#section-archive')

@login_required(login_url='login')
@user_passes_test(is_staff_or_teacher, login_url='home')
def calendar_event_permanent_delete(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    if request.method == 'POST':
        log_audit_event(request, 'delete', event, {'source': 'dashboard'})
        event.delete()
        messages.success(request, 'Calendar Event permanently deleted!')
        return redirect('/dashboard/#section-archive')
    return render(request, 'main/confirm_delete.html', {'object': event, 'permanent': True})

@login_required(login_url='login')
def bulk_archive_action(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST is allowed'}, status=400)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        model_type = data.get('model_type')
        ids = data.get('ids', [])
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid request data: {str(e)}'}, status=400)
    
    if not action or not model_type or not ids:
        return JsonResponse({'status': 'error', 'message': 'Missing action, model_type, or ids'}, status=400)
        
    if action not in ['restore', 'delete']:
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        
    is_admin = is_super_admin(request.user)
    is_staff_teacher = is_staff_or_teacher(request.user)
    
    if not is_staff_teacher and not is_admin:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    count = 0
    errors = []
    
    for pk in ids:
        try:
            if model_type == 'video':
                video = get_object_or_404(AnimationVideo, pk=pk)
                if not is_admin and video.author != request.user:
                    errors.append(f"Permission denied for Video ID {pk}")
                    continue
                if action == 'restore':
                    video.is_archived = False
                    video.save()
                    log_audit_event(request, 'restore', video, {'source': 'dashboard', 'bulk': True})
                elif action == 'delete':
                    log_audit_event(request, 'delete', video, {'source': 'dashboard', 'bulk': True})
                    video.delete()
                    
            elif model_type == 'flipbook':
                flipbook = get_object_or_404(Flipbook, pk=pk)
                if not is_admin and flipbook.author != request.user:
                    errors.append(f"Permission denied for Flipbook ID {pk}")
                    continue
                if action == 'restore':
                    flipbook.is_archived = False
                    flipbook.save()
                    log_audit_event(request, 'restore', flipbook, {'source': 'dashboard', 'bulk': True})
                elif action == 'delete':
                    log_audit_event(request, 'delete', flipbook, {'source': 'dashboard', 'bulk': True})
                    flipbook.delete()
                    
            elif model_type == 'announcement':
                if not is_admin:
                    errors.append(f"Permission denied for Announcement ID {pk}")
                    continue
                announcement = get_object_or_404(Announcement, pk=pk)
                if action == 'restore':
                    announcement.is_archived = False
                    announcement.save()
                    log_audit_event(request, 'restore', announcement, {'source': 'dashboard', 'bulk': True})
                elif action == 'delete':
                    log_audit_event(request, 'delete', announcement, {'source': 'dashboard', 'bulk': True})
                    announcement.delete()
                    
            elif model_type == 'user':
                if not is_admin:
                    errors.append(f"Permission denied for User ID {pk}")
                    continue
                if request.user.pk == pk and action == 'delete':
                    errors.append("You cannot delete your own account")
                    continue
                user = get_object_or_404(User, pk=pk)
                if action == 'restore':
                    if hasattr(user, 'profile'):
                        user.profile.is_archived = False
                        user.profile.save()
                    user.is_active = True
                    user.save()
                    log_audit_event(request, 'restore', user, {'source': 'dashboard', 'bulk': True}, target_label=user.username)
                elif action == 'delete':
                    log_audit_event(request, 'delete', user, {'source': 'dashboard', 'bulk': True}, target_label=user.username)
                    user.delete()
                    
            elif model_type == 'calendar':
                if not is_staff_teacher and not is_admin:
                    errors.append(f"Permission denied for Calendar Event ID {pk}")
                    continue
                event = get_object_or_404(CalendarEvent, pk=pk)
                if action == 'restore':
                    event.is_archived = False
                    event.save()
                    log_audit_event(request, 'restore', event, {'source': 'dashboard', 'bulk': True})
                elif action == 'delete':
                    log_audit_event(request, 'delete', event, {'source': 'dashboard', 'bulk': True})
                    event.delete()
            else:
                return JsonResponse({'status': 'error', 'message': f'Unknown model type: {model_type}'}, status=400)
                
            count += 1
        except Exception as ex:
            errors.append(f"Error processing {model_type} ID {pk}: {str(ex)}")
            
    if errors and count == 0:
        return JsonResponse({'status': 'error', 'message': "; ".join(errors)}, status=400)
    
    action_label = "restored" if action == 'restore' else "permanently deleted"
    msg = f"Successfully {action_label} {count} item(s)."
    if errors:
        msg += " Warnings: " + "; ".join(errors)
    return JsonResponse({'status': 'success', 'message': msg})

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def bulk_approval_action(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST is allowed'}, status=400)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        model_type = data.get('model_type')
        ids = data.get('ids', [])
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid request data: {str(e)}'}, status=400)
    
    if not action or not model_type or not ids:
        return JsonResponse({'status': 'error', 'message': 'Missing action, model_type, or ids'}, status=400)
        
    if action not in ['approve', 'deny']:
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        
    count = 0
    errors = []
    
    for pk in ids:
        try:
            if model_type == 'user':
                user = get_object_or_404(User, pk=pk)
                role_display = user.profile.get_role_display() if hasattr(user, 'profile') else 'User'
                if action == 'approve':
                    if hasattr(user, 'profile'):
                        user.profile.is_approved = True
                        user.profile.save()
                    if hasattr(user, 'profile') and user.profile.role == 'TEACHER':
                        user.is_staff = True
                    user.save()
                    
                    if user.email:
                        subject = "Account Approved - CraftyKids"
                        login_link = request.build_absolute_uri(reverse('login'))
                        message_body = (
                            f"Hello {user.first_name or user.username},\n\n"
                            f"Great news! Your account on CraftyKids has been approved by the Main Admin.\n\n"
                            f"You can now log in to your account and explore all our features:\n"
                            f"{login_link}\n\n"
                            f"Thank you,\n"
                            f"CraftyKids Team"
                        )
                        try:
                            send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [user.email])
                        except Exception as em:
                            print(f"Failed to send approval email: {em}")
                    
                    log_audit_event(request, 'approve', user, {'source': 'dashboard', 'bulk': True}, target_label=user.username)
                    
                elif action == 'deny':
                    username = user.username
                    if hasattr(user, 'profile'):
                        user.profile.is_archived = True
                        user.profile.save()
                    user.is_active = False
                    user.save()
                    log_audit_event(request, 'archive', user, {'source': 'dashboard', 'bulk': True}, target_label=username)
                    
            elif model_type == 'grade':
                user = get_object_or_404(User, pk=pk)
                if action == 'approve':
                    if hasattr(user, 'profile') and user.profile.pending_grade:
                        user.profile.grade_level = user.profile.pending_grade
                        user.profile.pending_grade = None
                        user.profile.save()
                        log_audit_event(request, 'approve_grade', user, {'source': 'dashboard', 'bulk': True}, target_label=user.username)
                elif action == 'deny':
                    if hasattr(user, 'profile'):
                        user.profile.pending_grade = None
                        user.profile.save()
                        log_audit_event(request, 'reject_grade', user, {'source': 'dashboard', 'bulk': True}, target_label=user.username)
                        
            elif model_type == 'video':
                video = get_object_or_404(AnimationVideo, pk=pk)
                if action == 'approve':
                    AnimationVideo.objects.filter(pk=pk).update(is_approved=True)
                    log_audit_event(request, 'approve', video, {'source': 'dashboard', 'bulk': True})
                elif action == 'deny':
                    log_audit_event(request, 'delete', video, {'source': 'dashboard', 'bulk': True})
                    video.delete()
                    
            elif model_type == 'flipbook':
                flipbook = get_object_or_404(Flipbook, pk=pk)
                if action == 'approve':
                    Flipbook.objects.filter(pk=pk).update(is_approved=True)
                    log_audit_event(request, 'approve', flipbook, {'source': 'dashboard', 'bulk': True})
                elif action == 'deny':
                    log_audit_event(request, 'delete', flipbook, {'source': 'dashboard', 'bulk': True})
                    flipbook.delete()
            else:
                errors.append(f"Unknown model type: {model_type}")
                continue
                
            count += 1
        except Exception as ex:
            errors.append(f"Error processing {model_type} ID {pk}: {str(ex)}")
            
    if errors and count == 0:
        return JsonResponse({'status': 'error', 'message': "; ".join(errors)}, status=400)
        
    action_label = "approved" if action == 'approve' else "denied"
    msg = f"Successfully {action_label} {count} item(s)."
    if errors:
        msg += " Warnings: " + "; ".join(errors)
    return JsonResponse({'status': 'success', 'message': msg})

@login_required(login_url='login')
@user_passes_test(is_super_admin, login_url='home')
def bulk_archive_announcements(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST is allowed'}, status=400)
    
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid request data: {str(e)}'}, status=400)
    
    if not ids:
        return JsonResponse({'status': 'error', 'message': 'No announcements selected'}, status=400)
        
    count = 0
    for pk in ids:
        try:
            announcement = get_object_or_404(Announcement, pk=pk)
            announcement.is_archived = True
            announcement.save()
            log_audit_event(request, 'archive', announcement, {'source': 'dashboard', 'bulk': True})
            count += 1
        except Exception:
            pass
            
    return JsonResponse({'status': 'success', 'message': f'Successfully archived {count} announcement(s).'})

# Teacher Tasks API
from django.views.decorators.http import require_POST
from datetime import datetime

@login_required(login_url='login')
@require_POST
def task_create_api(request):
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'status': 'error', 'message': 'Title is required'}, status=400)
            
        task = TeacherTask.objects.create(
            user=request.user,
            title=title,
            status='To Do'
        )
        return JsonResponse({
            'status': 'success',
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def task_update_api(request, task_id):
    try:
        task = get_object_or_404(TeacherTask, id=task_id, user=request.user)
        data = json.loads(request.body)
        
        if 'title' in data:
            task.title = data['title'].strip()
        if 'status' in data:
            task.status = data['status']
        if 'due_date' in data:
            due_date_str = data['due_date']
            if due_date_str:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            else:
                task.due_date = None
                
        task.save()
        return JsonResponse({
            'status': 'success',
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def task_delete_api(request, task_id):
    try:
        task = get_object_or_404(TeacherTask, id=task_id, user=request.user)
        task.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def increment_announcement_views(request, pk):
    try:
        announcement = get_object_or_404(Announcement, pk=pk)
        announcement.views += 1
        announcement.save(update_fields=['views'])
        return JsonResponse({'status': 'success', 'views': announcement.views})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

import random
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, "Please enter your email address.")
            return redirect('forgot_password')
        
        user = User.objects.filter(email=email).first()
        if user:
            code = str(random.randint(100000, 999999))
            PasswordResetCode.objects.filter(user=user).delete()
            PasswordResetCode.objects.create(user=user, code=code)
            
            subject = "Your Password Reset Code"
            message = f"Hello {user.first_name or user.username},\n\nYour password reset code is: {code}\nThis code will expire in 15 minutes.\n\nThank you,\nCraftyKids Team"
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                request.session['reset_email'] = email
                messages.success(request, "A 6-digit password reset code has been sent to your email.")
                return redirect('verify_reset_code')
            except Exception as e:
                messages.error(request, f"Failed to send email. Please ensure the email configuration is correct. ({str(e)})")
                return redirect('forgot_password')
        else:
            messages.error(request, "No account found with that email address.")
            return redirect('forgot_password')

    return render(request, 'main/forgot_password.html')

def verify_reset_code_view(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Session expired. Please request a new code.")
        return redirect('forgot_password')

    if request.method == 'POST':
        code = request.POST.get('code')
        user = User.objects.filter(email=email).first()
        if user:
            reset_obj = PasswordResetCode.objects.filter(user=user).first()
            if reset_obj and reset_obj.code == code:
                if timezone.now() > reset_obj.created_at + timedelta(minutes=15):
                    messages.error(request, "This code has expired. Please request a new one.")
                    reset_obj.delete()
                    return redirect('forgot_password')
                
                request.session['reset_verified'] = True
                reset_obj.delete()
                messages.success(request, "Code verified! Please enter your new password.")
                return redirect('reset_password')
            else:
                messages.error(request, "Invalid code. Please try again.")
        else:
            messages.error(request, "User not found.")
            return redirect('forgot_password')

    return render(request, 'main/verify_reset_code.html', {'email': email})

def reset_password_view(request):
    if not request.session.get('reset_verified'):
        messages.error(request, "Please verify your reset code first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('reset_password')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('reset_password')

        email = request.session.get('reset_email')
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(new_password)
            user.save()
            del request.session['reset_email']
            del request.session['reset_verified']
            messages.success(request, "Your password has been reset successfully. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "An error occurred. Please try again.")
            return redirect('forgot_password')

    return render(request, 'main/reset_password.html')