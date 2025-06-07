# users/tests/test_views.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core import mail
from users.models import Interest, UserInterest, PasswordReset
from django.utils import timezone

User = get_user_model()

class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'test@user.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'Testpass1!'
        }

    def test_register_success(self):
        resp = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('refresh', resp.data)
        self.assertIn('access', resp.data)
        self.assertEqual(resp.data['user']['email'], 'test@user.com')

    def test_login_success(self):
        User.objects.create_user(**self.user_data)
        resp = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_login_bad_credentials(self):
        resp = self.client.post(self.login_url, {
            'email': 'noone@nowhere.com',
            'password': 'wrong'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

class ProtectedEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('a@b.com', 'A', 'B', password='pass1234!')
        self.admin = User.objects.create_superuser('adm@in.com', 'Ad', 'Min', password='admin123!')
        self.home_url = reverse('home')
        self.users_list_url = reverse('users_list')

    def test_home_requires_auth(self):
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_home_returns_welcome(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Welcome to Home Page')

    def test_users_list_admin_only(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.users_list_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        resp2 = self.client.get(self.users_list_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

class InterestAndProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('x@y.com', 'X', 'Y', password='pass')
        self.client.force_authenticate(self.user)
        # create some interests
        self.i1 = Interest.objects.create(Title='A', Description='')
        self.i2 = Interest.objects.create(Title='B', Description='')

    def test_interest_list(self):
        resp = self.client.get(reverse('interests'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_save_user_interests(self):
        resp = self.client.post(reverse('save_interests'),
                                {'interests': [self.i1.InterestID, self.i2.InterestID]},
                                format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(UserInterest.objects.filter(UserID=self.user).count(), 2)

    def test_profile_get_and_update(self):
        # GET
        resp = self.client.get(reverse('user_profile'))
        self.assertEqual(resp.data['email'], self.user.email)
        # PUT
        resp2 = self.client.put(reverse('user_profile'),
                                {'first_name': 'NewName'}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewName')

class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('reset@me.com', 'R', 'E', password='OldPass1!')
        self.request_url = reverse('forget_password')
        mail.outbox = []

    def test_request_reset_valid_email(self):
        resp = self.client.post(self.request_url, {'email': self.user.email}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # one email sent
        self.assertEqual(len(mail.outbox), 1)
        pr = PasswordReset.objects.get(email=self.user.email)
        self.assertTrue(pr.token)

    def test_request_reset_invalid_email(self):
        resp = self.client.post(self.request_url, {'email': 'no@pe.no'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_password_flow(self):
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        token = PasswordResetTokenGenerator().make_token(self.user)
        PasswordReset.objects.create(email=self.user.email, token=token)
        url = reverse('reset_password', args=[token])
        resp = self.client.post(url,{
            'new_password': 'NewPass1@',
            'confirm_password': 'NewPass1@'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass1@'))
        # record deleted
        self.assertFalse(PasswordReset.objects.filter(token=token).exists())

class UpdateAccountTypeTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('adm@in.com','Ad','Min', password='p')
        self.client.force_authenticate(self.admin)
        self.target = User.objects.create_user('t@u.com','T','U', password='p')
        self.url = reverse('update_account_type', args=[self.target.PublicID])

    def test_update_account_type(self):
        resp = self.client.put(self.url, {'AccountType':'Admin'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertEqual(self.target.AccountType, 'Admin')

    def test_update_nonexistent(self):
        bad_url = reverse('update_account_type', args=['00000000-0000-0000-0000-000000000000'])
        resp = self.client.put(bad_url, {'AccountType':'User'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
