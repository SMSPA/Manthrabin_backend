# users/tests/test_serializers.py
from django.test import TestCase
from rest_framework import serializers
from users.serializers import (
    HomeSerializer, RegisterSerializer,
    ResetPasswordSerializer, UpdateAccountTypeSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()

# USER_INSTANCE = User.objects.create(email='', first_name='Jane', last_name='Doe', password='password123')

class HomeSerializerTests(TestCase):
    def test_get_account_type(self):
        user = User.objects.create_user('x@y.com', 'X', 'Y', 'p')
        user.account_type = 'Custom'
        data = HomeSerializer(user).data
        self.assertIn('message', data)
        self.assertEqual(data['account_type'], 'Custom')


class RegisterSerializerTests(TestCase):
    def test_create_calls_manager(self):
        data = {
            'email': 'new@user.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'Password1!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertTrue(User.objects.filter(email='new@user.com').exists())
        self.assertTrue(user.check_password('Password1!'))


class ResetPasswordSerializerTests(TestCase):
    def test_passwords_must_match(self):
        s = ResetPasswordSerializer(data={
            'new_password': 'Abcdef1@',
            'confirm_password': 'Mismatch1@'
        })
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def test_password_regex_enforced(self):
        s = ResetPasswordSerializer(data={
            'new_password': 'nopunct',
            'confirm_password': 'nopunct'
        })
        self.assertFalse(s.is_valid())
        self.assertIn('not match the required pattern', s.errors['new_password'][0])


class UpdateAccountTypeSerializerTests(TestCase):
    def test_invalid_choice(self):
        user = User.objects.create_user('a@b.com', 'A', 'B', password='p')
        s = UpdateAccountTypeSerializer(user, data={'AccountType': 'SuperUser'})
        self.assertFalse(s.is_valid())
        self.assertIn('AccountType', s.errors)
