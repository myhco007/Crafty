from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import AnimationVideo, AuditLog, Category


class AuditLogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Mathematics')
        self.staff_user = User.objects.create_user(
            username='admin',
            password='secret123',
            is_staff=True,
        )

    def test_register_creates_audit_log(self):
        response = self.client.post(
            reverse('register'),
            {
                'full_name': 'Test User',
                'email': 'test@example.com',
                'username': 'tester',
                'password1': 'strongpass123',
                'password2': 'strongpass123',
            },
        )

        self.assertRedirects(response, reverse('home'))
        self.assertTrue(AuditLog.objects.filter(action='register', target_label='tester').exists())

    def test_video_create_creates_audit_log(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse('video_create'),
            {
                'title': 'Counting Song',
                'description': 'Fun counting video',
                'category': self.category.pk,
                'duration': '03:20',
            },
        )

        self.assertRedirects(response, reverse('video_list'))
        video = AnimationVideo.objects.get(title='Counting Song')
        self.assertTrue(AuditLog.objects.filter(action='create', target_id=video.pk).exists())
