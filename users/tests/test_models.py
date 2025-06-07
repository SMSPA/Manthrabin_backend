# users/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import PasswordReset, Interest, UserInterest, User, UserManager
from django.core.exceptions import ValidationError


class UserModelTests(TestCase):
    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValidationError):
            user = User.objects.create(email='', first_name='Jane', last_name='Doe', password='password123')
            user.full_clean()

    def test_create_user_sets_fields_correctly(self):
        user = User.objects.create(
            email='jane@example.com',
            first_name='Jane',
            last_name='Doe',
            password='@@@asjdlkjaAApassword123'
        )
        user.save()
        self.assertEqual(user.email, 'jane@example.com')
        self.assertEqual(user.AccountType, 'User')
        self.assertEqual(User.objects.get(email="jane@example.com").password, '@@@asjdlkjaAApassword123')

    def test_create_admin_user_sets_admin_flags(self):
        admin = User.objects.create(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            AccountType='Admin',
            password='adminpass',
        )
        self.assertEqual(admin.AccountType, 'Admin')

    def test_str_returns_email(self):
        user = User.objects.create(email='foo@bar.com', first_name='Foo', last_name='Bar', password='adminpass')
        self.assertEqual(str(user), 'foo@bar.com')


class PasswordResetModelTests(TestCase):
    def test_password_reset_latest_by_created_at(self):
        # Create two resets; ensure get_latest_by works
        pr1 = PasswordReset.objects.create(email='a@b.com', token='t1')
        # advance time
        later = timezone.now() + timezone.timedelta(hours=1)
        with self.subTest("simulate later reset"):
            PasswordReset.objects.create(email='a@b.com', token='t2', created_at=later)
            self.assertEqual(PasswordReset.objects.latest(), PasswordReset.objects.get(token='t2'))


class InterestModelsTests(TestCase):
    def test_interest_str(self):
        interest = Interest.objects.create(Title='Django', Description='Web framework')
        self.assertEqual(str(interest), 'Django')

    def test_user_interest_unique_together(self):
        user = User.objects.create(email='u@i.com', first_name='U', last_name='I', password='p')
        interest = Interest.objects.create(Title='Test', Description='')
        UserInterest.objects.create(UserID=user, InterestID=interest)
        with self.assertRaises(Exception):
            UserInterest.objects.create(UserID=user, InterestID=interest)
