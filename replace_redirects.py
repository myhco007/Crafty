import sys

with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Video & Flipbook form/list redirects
content = content.replace("redirect('dashboard' if request.user.is_staff else 'video_list')", "redirect('/dashboard/#section-videos' if request.user.is_staff else 'video_list')")
content = content.replace("redirect('dashboard' if request.user.is_staff else 'flipbook_list')", "redirect('/dashboard/#section-flipbooks' if request.user.is_staff else 'flipbook_list')")

# Edit & Delete redirects that used to go to list
content = content.replace("redirect('video_list')", "redirect('/dashboard/#section-videos' if request.user.is_staff else 'video_list')")
content = content.replace("redirect('flipbook_list')", "redirect('/dashboard/#section-flipbooks' if request.user.is_staff else 'flipbook_list')")

# Archive redirects
# For toggle user status & delete user
content = content.replace("toggle_user_status(request, pk):\n    user = get_object_or_404(User, pk=pk)\n    user.is_active = not user.is_active\n    user.save()\n    log_audit_event(request, 'update', user, {'source': 'dashboard', 'status': 'active' if user.is_active else 'inactive'})\n    return redirect('dashboard')", 
"toggle_user_status(request, pk):\n    user = get_object_or_404(User, pk=pk)\n    user.is_active = not user.is_active\n    user.save()\n    log_audit_event(request, 'update', user, {'source': 'dashboard', 'status': 'active' if user.is_active else 'inactive'})\n    return redirect('/dashboard/#section-users')")

content = content.replace("delete_user(request, pk):\n    user = get_object_or_404(User, pk=pk)\n    if request.method == 'POST':\n        if hasattr(user, 'profile'):\n            user.profile.is_archived = True\n            user.profile.save()\n        user.is_active = False\n        user.save()\n        log_audit_event(request, 'archive', user, {'source': 'dashboard'})\n        messages.success(request, f'User {user.username} archived successfully!')\n        return redirect('dashboard')", 
"delete_user(request, pk):\n    user = get_object_or_404(User, pk=pk)\n    if request.method == 'POST':\n        if hasattr(user, 'profile'):\n            user.profile.is_archived = True\n            user.profile.save()\n        user.is_active = False\n        user.save()\n        log_audit_event(request, 'archive', user, {'source': 'dashboard'})\n        messages.success(request, f'User {user.username} archived successfully!')\n        return redirect('/dashboard/#section-users')")

# For user restore and delete
content = content.replace("def user_restore(request, pk):\n    user = get_object_or_404(User, pk=pk)\n    if hasattr(user, 'profile'):\n        user.profile.is_archived = False\n        user.profile.save()\n    user.is_active = True\n    user.save()\n    log_audit_event(request, 'restore', user, {'source': 'dashboard'})\n    messages.success(request, 'User account restored!')\n    return redirect('dashboard')",
"def user_restore(request, pk):\n    user = get_object_or_404(User, pk=pk)\n    if hasattr(user, 'profile'):\n        user.profile.is_archived = False\n        user.profile.save()\n    user.is_active = True\n    user.save()\n    log_audit_event(request, 'restore', user, {'source': 'dashboard'})\n    messages.success(request, 'User account restored!')\n    return redirect('/dashboard/#section-archive')")

content = content.replace("return redirect('dashboard')  # Self deletion protection", "return redirect('/dashboard/#section-users')  # Self deletion protection")

# Announcement
content = content.replace("def announcement_create(request):\n    if request.method == 'POST':\n        title = request.POST.get('title')\n        content_text = request.POST.get('content')\n        is_important = request.POST.get('is_important') == 'on'\n        \n        ann = Announcement.objects.create(\n            title=title,\n            content=content_text,\n            is_important=is_important,\n            author=request.user\n        )\n        log_audit_event(request, 'create', ann, {'source': 'dashboard'})\n        messages.success(request, 'Announcement posted!')\n        return redirect('dashboard')",
"def announcement_create(request):\n    if request.method == 'POST':\n        title = request.POST.get('title')\n        content_text = request.POST.get('content')\n        is_important = request.POST.get('is_important') == 'on'\n        \n        ann = Announcement.objects.create(\n            title=title,\n            content=content_text,\n            is_important=is_important,\n            author=request.user\n        )\n        log_audit_event(request, 'create', ann, {'source': 'dashboard'})\n        messages.success(request, 'Announcement posted!')\n        return redirect('/dashboard/#section-announcements')")

content = content.replace("def announcement_edit(request, pk):\n    announcement = get_object_or_404(Announcement, pk=pk)\n    form = AnnouncementForm(request.POST or None, instance=announcement)\n    if form.is_valid():\n        announcement = form.save()\n        log_audit_event(request, 'update', announcement, {'source': 'dashboard'})\n        messages.success(request, 'Announcement updated!')\n        return redirect('dashboard')",
"def announcement_edit(request, pk):\n    announcement = get_object_or_404(Announcement, pk=pk)\n    form = AnnouncementForm(request.POST or None, instance=announcement)\n    if form.is_valid():\n        announcement = form.save()\n        log_audit_event(request, 'update', announcement, {'source': 'dashboard'})\n        messages.success(request, 'Announcement updated!')\n        return redirect('/dashboard/#section-announcements')")

content = content.replace("def announcement_delete(request, pk):\n    announcement = get_object_or_404(Announcement, pk=pk)\n    if request.method == 'POST':\n        announcement.is_archived = True\n        announcement.save()\n        log_audit_event(request, 'archive', announcement, {'source': 'dashboard'})\n        messages.success(request, 'Announcement archived!')\n        return redirect('dashboard')",
"def announcement_delete(request, pk):\n    announcement = get_object_or_404(Announcement, pk=pk)\n    if request.method == 'POST':\n        announcement.is_archived = True\n        announcement.save()\n        log_audit_event(request, 'archive', announcement, {'source': 'dashboard'})\n        messages.success(request, 'Announcement archived!')\n        return redirect('/dashboard/#section-announcements')")

# Archive Restores
content = content.replace("def video_restore(request, pk):\n    video = get_object_or_404(AnimationVideo, pk=pk)\n    video.is_archived = False\n    video.save()\n    log_audit_event(request, 'restore', video, {'source': 'dashboard'})\n    messages.success(request, 'Video restored successfully!')\n    return redirect('dashboard')",
"def video_restore(request, pk):\n    video = get_object_or_404(AnimationVideo, pk=pk)\n    video.is_archived = False\n    video.save()\n    log_audit_event(request, 'restore', video, {'source': 'dashboard'})\n    messages.success(request, 'Video restored successfully!')\n    return redirect('/dashboard/#section-archive')")

content = content.replace("def flipbook_restore(request, pk):\n    flipbook = get_object_or_404(Flipbook, pk=pk)\n    flipbook.is_archived = False\n    flipbook.save()\n    log_audit_event(request, 'restore', flipbook, {'source': 'dashboard'})\n    messages.success(request, 'Flipbook restored successfully!')\n    return redirect('dashboard')",
"def flipbook_restore(request, pk):\n    flipbook = get_object_or_404(Flipbook, pk=pk)\n    flipbook.is_archived = False\n    flipbook.save()\n    log_audit_event(request, 'restore', flipbook, {'source': 'dashboard'})\n    messages.success(request, 'Flipbook restored successfully!')\n    return redirect('/dashboard/#section-archive')")

content = content.replace("def announcement_restore(request, pk):\n    announcement = get_object_or_404(Announcement, pk=pk)\n    announcement.is_archived = False\n    announcement.save()\n    log_audit_event(request, 'restore', announcement, {'source': 'dashboard'})\n    messages.success(request, 'Announcement restored!')\n    return redirect('dashboard')",
"def announcement_restore(request, pk):\n    announcement = get_object_or_404(Announcement, pk=pk)\n    announcement.is_archived = False\n    announcement.save()\n    log_audit_event(request, 'restore', announcement, {'source': 'dashboard'})\n    messages.success(request, 'Announcement restored!')\n    return redirect('/dashboard/#section-archive')")

# Permanent Deletes
content = content.replace("messages.success(request, 'Video permanently deleted!')\n        return redirect('dashboard')",
"messages.success(request, 'Video permanently deleted!')\n        return redirect('/dashboard/#section-archive')")
content = content.replace("messages.success(request, 'Flipbook permanently deleted!')\n        return redirect('dashboard')",
"messages.success(request, 'Flipbook permanently deleted!')\n        return redirect('/dashboard/#section-archive')")
content = content.replace("messages.success(request, 'User account permanently deleted!')\n        return redirect('dashboard')",
"messages.success(request, 'User account permanently deleted!')\n        return redirect('/dashboard/#section-archive')")
content = content.replace("messages.success(request, 'Announcement permanently deleted!')\n        return redirect('dashboard')",
"messages.success(request, 'Announcement permanently deleted!')\n        return redirect('/dashboard/#section-archive')")

with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
