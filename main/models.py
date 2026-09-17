from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

GRADE_CHOICES = [
    ('All Grades', 'All Grades'),
    ('Grade 1', 'Grade 1'),
    ('Grade 2', 'Grade 2'),
    ('Grade 3', 'Grade 3'),
    ('Grade 4', 'Grade 4'),
    ('Grade 5', 'Grade 5'),
    ('Grade 6', 'Grade 6'),
]

STUDENT_GRADE_CHOICES = [
    ('Grade 1', 'Grade 1'),
    ('Grade 2', 'Grade 2'),
    ('Grade 3', 'Grade 3'),
    ('Grade 4', 'Grade 4'),
    ('Grade 5', 'Grade 5'),
    ('Grade 6', 'Grade 6'),
]

class UserProfile(models.Model):
    ROLES = [
        ('SUPER_ADMIN', 'Main Admin'),
        ('TEACHER', 'Teacher'),
        ('CLIENT', 'Client/User'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLES, default='CLIENT')
    profile_picture = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # For teacher approval
    is_archived = models.BooleanField(default=False)  # For soft deleting users
    lrn_number = models.CharField(max_length=12, blank=True, null=True)
    section = models.CharField(max_length=50, blank=True, null=True)
    grade_level = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True, null=True)
    pending_grade = models.CharField(max_length=20, choices=STUDENT_GRADE_CHOICES, blank=True, null=True)
    grade_change_cooldown = models.DateTimeField(null=True, blank=True)
    last_seen_notifications = models.DateTimeField(null=True, blank=True)
    faculty_id_image = models.ImageField(upload_to='faculty_ids/', null=True, blank=True)

    # Expanded Profile Fields
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Category(models.Model):
    CATEGORY_CHOICES = [
        ('Mathematics', 'Mathematics'),
        ('MAPEH', 'MAPEH'),
        ('Science', 'Science'),
    ]
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)

    def __str__(self):
        return self.name


CRAFT_CHOICES = [
    ('All Categories', 'All Categories'),
    ('Toys & Games', 'Toys & Games (DIY PLAY)'),
    ('Role play & Imagination', 'Role play & Imagination'),
    ('Simple Science & Experiments', 'Simple Science & Experiments'),
    ('Home & Classroom decoration', 'Home & Classroom decoration'),
    ('Art & Creative crafts', 'Art & Creative crafts'),
    ('Paper & cardboard crafts', 'Paper & cardboard crafts'),
    ('Health & Hygiene', 'Health & Hygiene'),
    ('Nature & Eco - Friendly projects', 'Nature & Eco - Friendly projects'),
    ('Gifts & Holiday crafts', 'Gifts & Holiday crafts'),
    ('Skill - Building crafts', 'Skill - Building crafts'),
]


class AnimationVideo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    craft_category = models.CharField(max_length=50, choices=CRAFT_CHOICES, default='All Categories')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, default='All Grades')
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    duration = models.CharField(max_length=10, blank=True)  # e.g. "3:45"
    liked_by = models.ManyToManyField(User, related_name='liked_videos', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    
    # New Fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_videos')
    is_approved = models.BooleanField(default=True) # Default True for existing content

    def __str__(self):
        return self.title


class Flipbook(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='flipbooks')
    craft_category = models.CharField(max_length=50, choices=CRAFT_CHOICES, default='All Categories')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, default='All Grades')
    cover_image = models.ImageField(upload_to='flipbooks/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='flipbook_pdfs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(User, related_name='liked_flipbooks', blank=True)
    is_archived = models.BooleanField(default=False)
    
    # New Fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_flipbooks')
    is_approved = models.BooleanField(default=True) # Default True for existing content

    def __str__(self):
        return self.title


class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('Update', 'Update'),
        ('Activity', 'Activity'),
        ('Event', 'Event'),
        ('Holiday', 'Holiday'),
    ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Update')
    views = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New Fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_announcements')
    is_approved = models.BooleanField(default=True) # Default True for existing content
    is_archived = models.BooleanField(default=False)
    viewed_by = models.ManyToManyField(User, related_name='viewed_announcements', blank=True)
    target_audience = models.CharField(max_length=20, choices=[('Student', 'Student'), ('Teacher', 'Teacher')], default='Student')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, default='All Grades')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon = models.CharField(max_length=50, default='Star')
    link_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: target specific user (e.g. Super Admin)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    target_audience = models.CharField(max_length=20, choices=[('All', 'All'), ('Teacher', 'Teacher')], default='All')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('archive', 'Archived'),
        ('restore', 'Restored'),
        ('login', 'Logged in'),
        ('logout', 'Logged out'),
        ('register', 'Registered'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ]

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_label = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message


class VideoComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='video_comments')
    name = models.CharField(max_length=100, default='Anonymous')
    text = models.TextField()
    video = models.ForeignKey(AnimationVideo, on_delete=models.CASCADE, related_name='comments')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.text[:20]}"


class FlipbookComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='flipbook_comments')
    name = models.CharField(max_length=100, default='Anonymous')
    text = models.TextField()
    flipbook = models.ForeignKey(Flipbook, on_delete=models.CASCADE, related_name='comments')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.text[:20]}"

class StudentActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    video = models.ForeignKey('AnimationVideo', on_delete=models.CASCADE, null=True, blank=True)
    flipbook = models.ForeignKey('Flipbook', on_delete=models.CASCADE, null=True, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} completed activity on {self.completed_at}"


class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('Event', 'Event'),
        ('Holiday', 'Holiday'),
        ('Lesson Plan', 'Lesson Plan'),
        ('Module', 'Module'),
        ('Other', 'Other'),
        ('Todo', 'Todo'),
        ('Working On', 'Working On'),
        ('Stuck', 'Stuck'),
        ('Done', 'Done'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='Event')
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_events')
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} ({self.date})"


class TeacherTask(models.Model):
    STATUS_CHOICES = [
        ('To Do', 'To Do'),
        ('Working on it', 'Working on it'),
        ('Stuck', 'Stuck'),
        ('Done', 'Done'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To Do')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.code}"
