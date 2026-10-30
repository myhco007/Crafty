from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import AnimationVideo, AuditLog, Category, Flipbook


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
                'no_middle_name': '1',
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

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_register_exceeds_max_password_length(self, mock_recaptcha):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Test',
                'no_middle_name': '1',
                'last_name': 'User',
                'email': 'testmax@gmail.com',
                'username': 'testermax',
                'lrn_number': '123456789019',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'a_very_long_password15_chars_exceeded',
                'password2': 'a_very_long_password15_chars_exceeded',
            },
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('15 characters' in str(m) for m in messages))

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
                'no_middle_name': '1',
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
                'no_middle_name': '1',
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

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_register_without_middle_name_fails(self, mock_recaptcha):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'NoMiddle',
                'last_name': 'User',
                'email': 'nomiddle@gmail.com',
                'username': 'nomiddle_user',
                'lrn_number': '111122223333',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Middle Name' in str(m) for m in messages))

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_register_with_suffix_and_middle_name(self, mock_recaptcha):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Juan',
                'middle_name': 'Santos',
                'suffix': 'Jr.',
                'last_name': 'Dela Cruz',
                'email': 'juandelacruz@gmail.com',
                'username': 'juan_jr',
                'lrn_number': '555566667777',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='juan_jr')
        self.assertEqual(user.profile.middle_name, 'Santos')
        self.assertEqual(user.profile.suffix, 'Jr.')

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_reregister_unapproved_student_succeeds(self, mock_recaptcha):
        # Initial registration request (unapproved)
        self.client.post(
            reverse('register'),
            {
                'first_name': 'Juan',
                'no_middle_name': '1',
                'last_name': 'Dela Cruz',
                'email': 'unapproved_user@gmail.com',
                'username': 'unapproved_user',
                'lrn_number': '123412341234',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        user1 = User.objects.get(username='unapproved_user')
        self.assertFalse(user1.profile.is_approved)

        # Re-registering with same email/username/LRN but updated section
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Juan',
                'no_middle_name': '1',
                'last_name': 'Dela Cruz',
                'email': 'unapproved_user@gmail.com',
                'username': 'unapproved_user',
                'lrn_number': '123412341234',
                'grade_level': 'Grade 1',
                'section': '2',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        self.assertRedirects(response, reverse('login'))
        user2 = User.objects.get(username='unapproved_user')
        self.assertEqual(user2.profile.section, '1-2')
        self.assertFalse(user2.profile.is_approved)

    @patch('main.views.verify_recaptcha', return_value=True)
    def test_register_already_approved_email_fails(self, mock_recaptcha):
        approved_user = User.objects.create_user(
            username='approved_user',
            email='approved@gmail.com',
            password='strong_pass123'
        )
        approved_user.profile.is_approved = True
        approved_user.profile.save()

        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'New',
                'no_middle_name': '1',
                'last_name': 'User',
                'email': 'approved@gmail.com',
                'username': 'new_user',
                'lrn_number': '999988887777',
                'grade_level': 'Grade 1',
                'section': '1',
                'password1': 'strong_pass123',
                'password2': 'strong_pass123',
            },
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('already registered' in str(m) for m in messages))

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


class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='registered_student',
            email='registered@gmail.com',
            password='password123'
        )
        self.user.profile.is_approved = True
        self.user.profile.save()

    def test_new_user_sees_welcome_notification(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        notifs = response.context['notifications']
        self.assertEqual(len(notifs), 1)
        self.assertIn("Welcome to CraftyKids", notifs[0].title)

    def test_old_notifications_expire_after_seven_days(self):
        from datetime import timedelta
        from django.utils.timezone import now
        from main.models import Notification

        # Create an old notification 10 days ago
        old_notif = Notification.objects.create(
            title="Old Announcement",
            message="This is old news.",
            created_at=now() - timedelta(days=10)
        )
        Notification.objects.filter(pk=old_notif.pk).update(created_at=now() - timedelta(days=10))

        self.client.force_login(self.user)
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        notifs = list(response.context['notifications'])
        titles = [n.title for n in notifs]
        self.assertNotIn("Old Announcement", titles)


class FlipbookQuizTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Mathematics')
        self.teacher_user = User.objects.create_user(
            username='teacher_quiz',
            password='password123',
            email='teacher_quiz@gmail.com'
        )
        self.teacher_user.profile.role = 'TEACHER'
        self.teacher_user.profile.is_approved = True
        self.teacher_user.profile.save()

        self.student_user = User.objects.create_user(
            username='student_quiz',
            password='password123',
            email='student_quiz@gmail.com'
        )
        self.student_user.profile.role = 'CLIENT'
        self.student_user.profile.is_approved = True
        self.student_user.profile.save()

        self.flipbook = Flipbook.objects.create(
            title='Fun Math Story',
            description='Learn numbers!',
            category=self.category,
            author=self.teacher_user
        )

    def test_quiz_creation_and_question_addition(self):
        self.client.force_login(self.teacher_user)
        # GET quiz_manage view creates a FlipbookQuiz if none exists
        response = self.client.get(reverse('quiz_manage', kwargs={'pk': self.flipbook.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(self.flipbook, 'quiz'))

        # Add a question via POST
        response = self.client.post(
            reverse('quiz_manage', kwargs={'pk': self.flipbook.pk}),
            {
                'add_question': '1',
                'question-question_text': 'What is 2 + 2?',
                'question-option_a': '4',
                'question-option_b': '3',
                'question-option_c': '5',
                'question-option_d': '2',
                'question-correct_option': 'A',
                'question-order': 1
            }
        )
        self.assertRedirects(response, reverse('quiz_manage', kwargs={'pk': self.flipbook.pk}))
        self.assertEqual(self.flipbook.quiz.questions.count(), 1)
        question = self.flipbook.quiz.questions.first()
        self.assertEqual(question.question_text, 'What is 2 + 2?')
        self.assertEqual(question.correct_option, 'A')

    def test_student_quiz_submission_and_bonus_stars(self):
        from main.models import FlipbookQuiz, FlipbookQuestion, StudentQuizAttempt
        quiz = FlipbookQuiz.objects.create(flipbook=self.flipbook, pass_percentage=50)
        q1 = FlipbookQuestion.objects.create(
            quiz=quiz,
            question_text='What color is the sky?',
            option_a='Blue',
            option_b='Green',
            correct_option='A',
            order=1
        )
        q2 = FlipbookQuestion.objects.create(
            quiz=quiz,
            question_text='What is 5 + 5?',
            option_a='12',
            option_b='10',
            correct_option='B',
            order=2
        )

        self.client.force_login(self.student_user)
        import json
        
        # Submit correct answers to both questions
        response = self.client.post(
            reverse('submit_flipbook_quiz'),
            data=json.dumps({
                'flipbook_id': self.flipbook.pk,
                'answers': {
                    str(q1.pk): 'A',
                    str(q2.pk): 'B'
                }
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['passed'])
        self.assertEqual(data['score'], 2)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['stars_awarded'], 30)

        # Verify StudentQuizAttempt record created
        self.assertEqual(StudentQuizAttempt.objects.filter(user=self.student_user, quiz=quiz).count(), 1)
        
        # Verify points awarded to student profile (+30)
        self.student_user.profile.refresh_from_db()
        self.assertEqual(self.student_user.profile.points, 30)

        # Retake quiz and pass again -> score should be updated, but no extra stars awarded
        response2 = self.client.post(
            reverse('submit_flipbook_quiz'),
            data=json.dumps({
                'flipbook_id': self.flipbook.pk,
                'answers': {
                    str(q1.pk): 'A',
                    str(q2.pk): 'B'
                }
            }),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertTrue(data2['passed'])
        self.assertEqual(data2['stars_awarded'], 0)
        self.student_user.profile.refresh_from_db()
        self.assertEqual(self.student_user.profile.points, 30)

    def test_flipbook_tagalog_language_toggle(self):
        self.flipbook.title_tl = "Paghuhugas ng Kamay"
        self.flipbook.description_tl = "Isang simpleng paraan upang maging malinis."
        self.flipbook.save()

        self.client.force_login(self.student_user)
        response = self.client.get(reverse('flipbook_detail', kwargs={'pk': self.flipbook.pk}) + '?lang=tl')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_lang'], 'tl')
        self.assertContains(response, "Paghuhugas ng Kamay")

    def test_content_ordering_newest_first(self):
        f2 = Flipbook.objects.create(
            title='Newest Story Book',
            description='Brand new content',
            category=self.category,
            author=self.teacher_user
        )
        response = self.client.get(reverse('flipbook_list'))
        self.assertEqual(response.status_code, 200)
        flipbooks = list(response.context['flipbooks'])
        self.assertEqual(flipbooks[0], f2)


class FlipbookUploadAndValidationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Science')
        import io
        import pypdf

        # Create 1-page PDF
        writer1 = pypdf.PdfWriter()
        writer1.add_blank_page(width=200, height=200)
        buf1 = io.BytesIO()
        writer1.write(buf1)
        self.single_page_pdf_data = buf1.getvalue()

        # Create 2-page PDF
        writer2 = pypdf.PdfWriter()
        writer2.add_blank_page(width=200, height=200)
        writer2.add_blank_page(width=200, height=200)
        buf2 = io.BytesIO()
        writer2.write(buf2)
        self.multi_page_pdf_data = buf2.getvalue()

    def test_flipbook_rejects_single_page_pdf(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.forms import FlipbookForm

        pdf = SimpleUploadedFile('cover_poster.pdf', self.single_page_pdf_data, content_type='application/pdf')
        form = FlipbookForm(
            data={
                'title': 'Single Page Craft',
                'description': 'Description',
                'category': self.category.pk,
                'craft_category': 'Paper & cardboard crafts',
                'grade': 'Grade 1'
            },
            files={'pdf_file': pdf}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file', form.errors)
        self.assertTrue(any('at least 2 pages' in str(e) for e in form.errors['pdf_file']))

    def test_flipbook_rejects_image_as_pdf(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.forms import FlipbookForm

        fake_image = SimpleUploadedFile('craft_picture.jpg', b'fake image data', content_type='image/jpeg')
        form = FlipbookForm(
            data={
                'title': 'Invalid Craft',
                'description': 'Description',
                'category': self.category.pk,
                'craft_category': 'Paper & cardboard crafts',
                'grade': 'Grade 1'
            },
            files={'pdf_file': fake_image}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file', form.errors)
        self.assertTrue(any('valid PDF' in str(e) for e in form.errors['pdf_file']))

    def test_flipbook_accepts_multipage_pdf(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.forms import FlipbookForm

        pdf = SimpleUploadedFile('tutorial_book.pdf', self.multi_page_pdf_data, content_type='application/pdf')
        audio = SimpleUploadedFile('story.mp3', b'fake audio data', content_type='audio/mpeg')
        form = FlipbookForm(
            data={
                'title': 'Complete Multi-Page Craft Tutorial',
                'description': 'Description',
                'category': self.category.pk,
                'craft_category': 'Paper & cardboard crafts',
                'grade': 'Grade 1'
            },
            files={'pdf_file': pdf, 'audio_file': audio}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_flipbook_grade_1_requires_audio(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.forms import FlipbookForm

        pdf = SimpleUploadedFile('tutorial_book.pdf', self.multi_page_pdf_data, content_type='application/pdf')
        form = FlipbookForm(
            data={
                'title': 'Grade 1 Craft without Audio',
                'description': 'Description',
                'category': self.category.pk,
                'craft_category': 'Paper & cardboard crafts',
                'grade': 'Grade 1'
            },
            files={'pdf_file': pdf}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('audio_file', form.errors)
        self.assertTrue(any('Grade 1–3 flipbooks require an audio narration' in str(e) for e in form.errors['audio_file']))

    def test_flipbook_grade_4_does_not_require_audio(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.forms import FlipbookForm

        pdf = SimpleUploadedFile('tutorial_book.pdf', self.multi_page_pdf_data, content_type='application/pdf')
        form = FlipbookForm(
            data={
                'title': 'Grade 4 Craft without Audio',
                'description': 'Description',
                'category': self.category.pk,
                'craft_category': 'Paper & cardboard crafts',
                'grade': 'Grade 4'
            },
            files={'pdf_file': pdf}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_flipbook_edit_without_new_file_keeps_existing(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.forms import FlipbookForm

        pdf = SimpleUploadedFile('initial.pdf', self.multi_page_pdf_data, content_type='application/pdf')
        audio = SimpleUploadedFile('story.mp3', b'fake audio data', content_type='audio/mpeg')
        flipbook = Flipbook.objects.create(
            title='Existing Book',
            description='Original',
            category=self.category,
            grade='Grade 1',
            pdf_file=pdf,
            audio_file=audio
        )

        form = FlipbookForm(
            data={
                'title': 'Existing Book Renamed',
                'description': 'Updated description',
                'category': self.category.pk,
                'craft_category': 'Paper & cardboard crafts',
                'grade': 'Grade 1'
            },
            instance=flipbook
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated.title, 'Existing Book Renamed')
        self.assertTrue(updated.pdf_file)
        self.assertTrue(updated.audio_file)






