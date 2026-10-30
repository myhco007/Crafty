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
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    
    SUFFIX_CHOICES = [
        ('', 'None'),
        ('Jr.', 'Jr.'),
        ('Sr.', 'Sr.'),
        ('I', 'I'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
        ('V', 'V'),
    ]
    suffix = models.CharField(max_length=10, choices=SUFFIX_CHOICES, blank=True, null=True)
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
    points = models.PositiveIntegerField(default=0)

    def get_level_info(self):
        pts = self.points
        levels = [
            (1, "Novice Crafter", 0, 150),
            (2, "Junior Maker", 150, 450),
            (3, "Story Master", 450, 1000),
            (4, "Craft Explorer", 1000, 2000),
            (5, "Legend Crafter", 2000, 2000),
        ]
        
        for lvl, title, min_p, max_p in levels:
            if lvl == 5:
                return {
                    'level': 5,
                    'title': title,
                    'points': pts,
                    'min_points': min_p,
                    'max_points': max_p,
                    'progress_pct': 100,
                    'stars_needed': 0
                }
            if pts < max_p:
                range_pts = max_p - min_p
                current_in_lvl = max(0, pts - min_p)
                pct = int((current_in_lvl / range_pts) * 100) if range_pts > 0 else 100
                return {
                    'level': lvl,
                    'title': title,
                    'points': pts,
                    'min_points': min_p,
                    'max_points': max_p,
                    'progress_pct': min(100, max(0, pct)),
                    'stars_needed': max_p - pts
                }
        return {
            'level': 1,
            'title': "Novice Crafter",
            'points': pts,
            'min_points': 0,
            'max_points': 150,
            'progress_pct': 0,
            'stars_needed': 150
        }

    def get_badges_info(self):
        user = self.user
        completed_flipbooks = user.activities.filter(flipbook__isnull=False).count()
        completed_videos = user.activities.filter(video__isnull=False).count()
        total_completed = user.activities.count()
        total_likes = user.liked_videos.count() + user.liked_flipbooks.count()
        completed_quizzes = user.quiz_attempts.filter(passed=True).count() if hasattr(user, 'quiz_attempts') else 0
        total_comments = (user.video_comments.count() if hasattr(user, 'video_comments') else 0) + (user.flipbook_comments.count() if hasattr(user, 'flipbook_comments') else 0)

        badges = [
            {
                'id': 'first_flipbook',
                'icon': '📖',
                'name': 'First Page Turner',
                'desc': 'Finished reading your 1st Flipbook',
                'unlocked': completed_flipbooks >= 1
            },
            {
                'id': 'bookworm',
                'icon': '📚',
                'name': 'Bookworm Legend',
                'desc': 'Finished reading 5 Flipbooks',
                'unlocked': completed_flipbooks >= 5
            },
            {
                'id': 'first_video',
                'icon': '🎬',
                'name': 'Video Explorer',
                'desc': 'Completed watching 1st Video Tutorial',
                'unlocked': completed_videos >= 1
            },
            {
                'id': 'craft_master',
                'icon': '🌟',
                'name': 'Craft Master',
                'desc': 'Completed 10 total learning activities',
                'unlocked': total_completed >= 10
            },
            {
                'id': 'quiz_master',
                'icon': '🧠',
                'name': 'Quiz Master',
                'desc': 'Passed 3 Flipbook Assessments',
                'unlocked': completed_quizzes >= 3
            },
            {
                'id': 'supporter',
                'icon': '❤️',
                'name': 'Super Supporter',
                'desc': 'Liked 5 flipbooks or videos',
                'unlocked': total_likes >= 5
            },
            {
                'id': 'friendly',
                'icon': '💬',
                'name': 'Friendly Crafter',
                'desc': 'Posted 3 comments on crafts',
                'unlocked': total_comments >= 3
            },
        ]
        return badges

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

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title


class Flipbook(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    title_tl = models.CharField(max_length=200, blank=True, null=True)
    description_tl = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='flipbooks')
    craft_category = models.CharField(max_length=50, choices=CRAFT_CHOICES, default='All Categories')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, default='All Grades')
    cover_image = models.ImageField(upload_to='flipbooks/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='flipbook_pdfs/', blank=True, null=True)
    audio_file = models.FileField(upload_to='flipbook_audios/', blank=True, null=True, help_text="Upload 1 audio narration file (MP3/M4A/WAV). Required for Grades 1-3.")
    audio_file_tl = models.FileField(upload_to='flipbook_audios/', blank=True, null=True, help_text="Optional Tagalog narration (MP3/M4A/WAV).")
    silent_pages = models.CharField(max_length=200, blank=True, default='', help_text="Comma-separated page numbers without dialogue (e.g. 1, 3, 5). Audio will stop on these pages.")
    page_timestamps = models.CharField(max_length=255, blank=True, default='', help_text="Optional comma-separated start times for pages (e.g. 0:00, 0:15, 0:32). If blank, timings are automatically divided equally!")
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(User, related_name='liked_flipbooks', blank=True)
    is_archived = models.BooleanField(default=False)
    
    # New Fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_flipbooks')
    is_approved = models.BooleanField(default=True) # Default True for existing content

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title

    @property
    def has_audio(self):
        return bool(self.audio_file or self.audio_file_tl)

    def get_silent_pages_list(self):
        if not self.silent_pages:
            return []
        pages = []
        for p in self.silent_pages.replace(';', ',').split(','):
            p = p.strip()
            if p.isdigit():
                pages.append(int(p))
        return pages

    def get_timestamps_list(self):
        if not self.page_timestamps:
            return []
        timestamps = []
        for item in self.page_timestamps.replace(';', ',').split(','):
            item = item.strip()
            if not item:
                continue
            if ':' in item:
                parts = item.split(':')
                try:
                    if len(parts) == 2:
                        seconds = int(parts[0]) * 60 + float(parts[1])
                        timestamps.append(round(seconds, 2))
                    elif len(parts) == 3:
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                        timestamps.append(round(seconds, 2))
                except ValueError:
                    pass
            else:
                try:
                    timestamps.append(round(float(item), 2))
                except ValueError:
                    pass
        return timestamps


class FlipbookPageAudio(models.Model):
    """Stores a per-page audio file for a Flipbook. One record per page."""
    flipbook = models.ForeignKey(Flipbook, on_delete=models.CASCADE, related_name='page_audios')
    page_number = models.PositiveIntegerField(help_text="1-indexed page number this audio belongs to.")
    audio_file = models.FileField(upload_to='flipbook_page_audios/', help_text="MP3 audio for this specific page.")

    class Meta:
        ordering = ['page_number']
        unique_together = ('flipbook', 'page_number')

    def __str__(self):
        return f"{self.flipbook.title} – Page {self.page_number}"


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


class FlipbookQuiz(models.Model):
    flipbook = models.OneToOneField(Flipbook, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200, default='Flipbook Assessment')
    pass_percentage = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz for {self.flipbook.title}"


class FlipbookQuestion(models.Model):
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    quiz = models.ForeignKey(FlipbookQuiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES, default='A')
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:30]}"


class StudentQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(FlipbookQuiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    passed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} scored {self.score}/{self.total_questions} on {self.quiz.flipbook.title}"
