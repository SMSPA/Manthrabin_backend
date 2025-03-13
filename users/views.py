from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Interest, UserInterest
from .serializers import RegisterSerializer, UserSerializer, InterestSerializer, UserProfileUpdateSerializer, PasswordChangeSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Automatically log in the user after registration
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'redirect_to': '/select-interests'  # Redirect new users to interests page
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class HomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'message': 'Welcome to Home Page',
            'account_type': request.user.AccountType  # Send account type to frontend
        })

class UsersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only allow access if the user is an Admin
        if request.user.AccountType != "Admin":
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class InterestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interests = Interest.objects.all()
        serializer = InterestSerializer(interests, many=True)
        return Response(serializer.data)

class SaveUserInterestsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        selected_interest_ids = request.data.get("interests", [])

        # Delete existing interests
        UserInterest.objects.filter(UserID=user).delete()

        # Add new interests
        for interest_id in selected_interest_ids:
            interest = Interest.objects.get(InterestID=interest_id)
            UserInterest.objects.create(UserID=user, InterestID=interest)

        return Response({"message": "Interests saved successfully."}, status=status.HTTP_200_OK)


# Profile
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data.get('current_password')
            new_password = serializer.validated_data.get('new_password')

            # verify current password
            if not user.check_password(current_password):
                return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

            # Set new password
            user.set_password(new_password)
            user.save()

            # Generate new token
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Password changed successfully',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
