from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

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

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_register_creates_audit_log(self, mock_recaptcha):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@gmail.com',
                'username': 'tester',
                'lrn_number': '123456789012',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(AuditLog.objects.filter(action='register', target_label='tester').exists())

    def test_video_create_creates_audit_log(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse('video_create'),
            {
                'title': 'Counting Song',
                'description': 'Fun counting video',
                'category': self.category.pk,
                'craft_category': 'Toys & Games',
                'grade': 'Grade 1',
            },
        )

        if response.status_code == 200:
            print("Form errors:", response.context['form'].errors)

        self.assertRedirects(response, '/dashboard/#section-videos')
        video = AnimationVideo.objects.get(title='Counting Song')
        self.assertTrue(AuditLog.objects.filter(action='create', target_id=video.pk).exists())

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_register_sends_email(self, mock_recaptcha):
        from django.core import mail
        mail.outbox = []
        
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Student',
                'last_name': 'Test',
                'email': 'student@gmail.com',
                'username': 'student_test',
                'lrn_number': '987654321012',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Registration Submitted", mail.outbox[0].subject)
        self.assertIn("student@gmail.com", mail.outbox[0].to)
        
    @patch('main.views.verify_recaptcha', return_value=True)
    def test_teacher_register_sends_email(self, mock_recaptcha):
        from django.core import mail
        mail.outbox = []
        
        response = self.client.post(
            reverse('teacher_register'),
            {
                'first_name': 'Teacher',
                'last_name': 'Test',
                'email': 'teacher@gmail.com',
                'username': 'teacher_test',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Registration Submitted", mail.outbox[0].subject)
        self.assertIn("teacher@gmail.com", mail.outbox[0].to)

    def test_approve_user_sends_email(self):
        from django.core import mail
        mail.outbox = []
        
        pending_user = User.objects.create_user(
            username='pending_student',
            email='pending_student@gmail.com',
            password='strong_pass123'
        )
        pending_user.profile.is_approved = False
        pending_user.profile.save()
        
        super_admin = User.objects.create_superuser(
            username='superadmin',
            password='super_password123',
            email='super@gmail.com'
        )
        super_admin.profile.role = 'SUPER_ADMIN'
        super_admin.profile.save()
        self.client.force_login(super_admin)
        
        response = self.client.post(
            reverse('approve_user', kwargs={'pk': pending_user.pk}),
            {}
        )
        self.assertRedirects(response, '/dashboard/#section-pending')
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Account Approved", mail.outbox[0].subject)
        self.assertIn("pending_student@gmail.com", mail.outbox[0].to)


class BulkApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            password='super_password123',
            email='super@gmail.com'
        )
        self.super_admin.profile.role = 'SUPER_ADMIN'
        self.super_admin.profile.save()
        
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='teacher_password123',
            email='teacher@gmail.com'
        )
        self.teacher_user.profile.role = 'TEACHER'
        self.teacher_user.profile.save()

        # Create some pending student users
        self.pending_student1 = User.objects.create_user(
            username='pending1',
            email='pending1@gmail.com',
            password='strong_pass123'
        )
        self.pending_student1.profile.is_approved = False
        self.pending_student1.profile.grade_level = 'Grade 1'
        self.pending_student1.profile.save()

        self.pending_student2 = User.objects.create_user(
            username='pending2',
            email='pending2@gmail.com',
            password='strong_pass123'
        )
        self.pending_student2.profile.is_approved = False
        self.pending_student2.profile.grade_level = 'Grade 2'
        self.pending_student2.profile.save()

    def test_bulk_approve_users(self):
        self.client.force_login(self.super_admin)
        import json
        response = self.client.post(
            reverse('bulk_approval_action'),
            data=json.dumps({
                'action': 'approve',
                'model_type': 'user',
                'ids': [self.pending_student1.pk, self.pending_student2.pk]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Successfully approved 2 item(s)', data['message'])
        
        # Verify both are approved now
        self.pending_student1.refresh_from_db()
        self.pending_student2.refresh_from_db()
        self.assertTrue(self.pending_student1.profile.is_approved)
        self.assertTrue(self.pending_student2.profile.is_approved)

    def test_bulk_deny_users(self):
        self.client.force_login(self.super_admin)
        import json
        response = self.client.post(
            reverse('bulk_approval_action'),
            data=json.dumps({
                'action': 'deny',
                'model_type': 'user',
                'ids': [self.pending_student1.pk, self.pending_student2.pk]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Successfully denied 2 item(s)', data['message'])

        # Verify they are archived/inactive
        self.pending_student1.refresh_from_db()
        self.pending_student2.refresh_from_db()
        self.assertFalse(self.pending_student1.is_active)
        self.assertFalse(self.pending_student2.is_active)
        self.assertTrue(self.pending_student1.profile.is_archived)
        self.assertTrue(self.pending_student2.profile.is_archived)

    def test_bulk_approval_unauthorized(self):
        # Teacher is not a super admin, should be rejected/redirected
        self.client.force_login(self.teacher_user)
        import json
        response = self.client.post(
            reverse('bulk_approval_action'),
            data=json.dumps({
                'action': 'approve',
                'model_type': 'user',
                'ids': [self.pending_student1.pk]
            }),
            content_type='application/json'
        )
        # Should redirect to home or login because user_passes_test(is_super_admin) redirects by default
        self.assertEqual(response.status_code, 302)


