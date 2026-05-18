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
        fields = ['title', 'content', 'category', 'is_active']

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
