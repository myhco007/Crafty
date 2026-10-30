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


from django.core.files.uploadedfile import UploadedFile

class FlipbookForm(forms.ModelForm):
    class Meta:
        model = Flipbook
        fields = [
            'title', 'title_tl', 'description', 'description_tl',
            'category', 'craft_category', 'grade',
            'cover_image', 'pdf_file',
        ]
        labels = {
            'title_tl': 'Tagalog Title (Optional)',
            'description_tl': 'Tagalog Description (Optional)',
            'category': 'Subject',
            'craft_category': 'Category',
            'cover_image': 'Cover Image (Thumbnail)',
            'pdf_file': 'Tutorial PDF (Multi-Page PDF)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'cover_image' in self.fields:
            self.fields['cover_image'].widget.attrs.update({'accept': 'image/*'})
            self.fields['cover_image'].help_text = "Upload a cover/thumbnail image (PNG, JPG, WEBP)."
        if 'pdf_file' in self.fields:
            self.fields['pdf_file'].widget.attrs.update({'accept': '.pdf,application/pdf'})
            self.fields['pdf_file'].help_text = "Upload the complete tutorial as a multi-page PDF (at least 2 pages)."

    def clean_cover_image(self):
        cover = self.cleaned_data.get('cover_image')
        if cover and isinstance(cover, UploadedFile):
            valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
            if not cover.name.lower().endswith(valid_extensions):
                raise forms.ValidationError("Please upload a valid image file (PNG, JPG, JPEG, WEBP) for the cover.")
        return cover

    def clean_pdf_file(self):
        pdf = self.cleaned_data.get('pdf_file')
        if pdf and isinstance(pdf, UploadedFile):
            name = pdf.name.lower()
            if not name.endswith('.pdf'):
                raise forms.ValidationError(
                    "Invalid file type. Please upload a valid PDF document (.pdf). Images must be uploaded to the Cover Image field."
                )
            try:
                import pypdf
                reader = pypdf.PdfReader(pdf)
                num_pages = len(reader.pages)
                pdf.seek(0)
                if num_pages < 2:
                    raise forms.ValidationError(
                        f"The uploaded PDF has only {num_pages} page. A flipbook tutorial must contain at least 2 pages so readers can flip through the tutorial."
                    )
            except forms.ValidationError:
                raise
            except Exception:
                pass
        return pdf


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


from .models import FlipbookQuiz, FlipbookQuestion

class FlipbookQuizForm(forms.ModelForm):
    class Meta:
        model = FlipbookQuiz
        fields = ['title', 'pass_percentage']
        labels = {
            'pass_percentage': 'Passing Score (%)'
        }


class FlipbookQuestionForm(forms.ModelForm):
    class Meta:
        model = FlipbookQuestion
        fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'order']
        labels = {
            'question_text': 'Question',
            'option_a': 'Option A',
            'option_b': 'Option B',
            'option_c': 'Option C (Optional)',
            'option_d': 'Option D (Optional)',
            'correct_option': 'Correct Option Answer',
        }
