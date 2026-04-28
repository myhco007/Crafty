from django import forms
from .models import AnimationVideo, Flipbook, Announcement


class AnimationVideoForm(forms.ModelForm):
    class Meta:
        model = AnimationVideo
        fields = ['title', 'description', 'category', 'craft_category', 'grade', 'video_file', 'thumbnail', 'duration']
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
        fields = ['title', 'content', 'is_active']

