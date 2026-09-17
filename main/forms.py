from django import forms
from .models import AnimationVideo, Flipbook, Announcement, CalendarEvent

class AnimationVideoForm(forms.ModelForm):
    class Meta:
        model = AnimationVideo
        fields = ['title', 'description', 'category', 'craft_category', 'grade', 'video_file', 'thumbnail']
        labels = {
            'category': 'Subject',
            'craft_category': 'Category'
        }


class FlipbookForm(forms.ModelForm):
    class Meta:
        model = Flipbook
        fields = ['title', 'description', 'category', 'craft_category', 'grade', 'cover_image', 'pdf_file']
        labels = {
            'category': 'Subject',
            'craft_category': 'Category'
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'target_audience', 'grade', 'is_active']

from django.contrib.auth.models import User
from .models import UserProfile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']

from .models import UserProfile, STUDENT_GRADE_CHOICES

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'grade_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'grade_level' in self.fields:
            self.fields['grade_level'].choices = [('', '---------')] + STUDENT_GRADE_CHOICES



class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'date', 'event_type', 'image']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and hasattr(self.user, 'profile'):
            if self.user.profile.role == 'TEACHER':
                self.fields['event_type'].choices = [
                    ('Todo', 'Todo'),
                    ('Working On', 'Working On'),
                    ('Stuck', 'Stuck'),
                    ('Done', 'Done'),
                ]
            elif self.user.profile.role == 'SUPER_ADMIN':
                self.fields['event_type'].choices = [c for c in CalendarEvent.EVENT_TYPES if c[0] not in ['Lesson Plan', 'Module']]
