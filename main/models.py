from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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


GRADE_CHOICES = [
    ('All Grades', 'All Grades'),
    ('Grade 1', 'Grade 1'),
    ('Grade 2', 'Grade 2'),
    ('Grade 3', 'Grade 3'),
    ('Grade 4', 'Grade 4'),
    ('Grade 5', 'Grade 5'),
    ('Grade 6', 'Grade 6'),
]


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
    heyzine_url = models.URLField(max_length=500, blank=True, null=True)
    liked_by = models.ManyToManyField(User, related_name='liked_flipbooks', blank=True)
    is_archived = models.BooleanField(default=False)
    
    # New Fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_flipbooks')
    is_approved = models.BooleanField(default=True) # Default True for existing content

    def __str__(self):
        return self.title


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New Fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_announcements')
    is_approved = models.BooleanField(default=True) # Default True for existing content

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


class Comment(models.Model):
    name = models.CharField(max_length=100, default='Anonymous')
    text = models.TextField()
    video = models.ForeignKey(AnimationVideo, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    flipbook = models.ForeignKey(Flipbook, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.text[:20]}"
