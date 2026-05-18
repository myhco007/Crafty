import sys

with open('main/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    context = "".join(lines[max(0, i-30):i+1])
    
    if "return redirect('dashboard')" in line:
        if 'toggle_user_status' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-users')")
        elif 'delete_user' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-users')")
        elif 'user_restore' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'user_permanent_delete' in context:
            if 'Self deletion' in line:
                lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-users')")
            else:
                lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'announcement_create' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-announcements')")
        elif 'announcement_edit' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-announcements')")
        elif 'announcement_delete' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-announcements')")
        elif 'announcement_restore' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'announcement_permanent_delete' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'video_restore' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'video_permanent_delete' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'flipbook_restore' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")
        elif 'flipbook_permanent_delete' in context:
            lines[i] = line.replace("redirect('dashboard')", "redirect('/dashboard/#section-archive')")

with open('main/views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Done")
