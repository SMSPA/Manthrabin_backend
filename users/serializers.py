from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import User, Interest, UserInterest


class HomeSerializer(serializers.Serializer):
    message = serializers.CharField(default="Welcome to Home Page")
    account_type = serializers.SerializerMethodField()

    def get_account_type(self, obj) -> str:
        return getattr(obj, 'account_type', None)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["PublicID", "email", "first_name", "last_name",
                  "AccountType", "IsActive", "Created_at"]


class LoginInputSerializer(serializers.Serializer):
    # Input fields
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    # Output fields
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = "__all__"


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.RegexField(
        regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
        write_only=True,
        error_messages={
            'error': (
                'Password must be at least 8 characters long with at least one capital letter and symbol')})
    confirm_password = serializers.CharField(
        write_only=True,
        required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'error': "Passwords do not match."})
        return data


class UpdateAccountTypeSerializer(serializers.ModelSerializer):
    AccountType = serializers.ChoiceField(choices=User.ACCOUNT_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ['AccountType']
