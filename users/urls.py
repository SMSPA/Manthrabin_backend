from django.urls import path
from .views import RegisterView, LoginView, HomeView, UsersListView, InterestListView, SaveUserInterestsView, UserProfileView, ChangePasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('home/', HomeView.as_view(), name='home'),
    path("users/", UsersListView.as_view(), name="users_list"),
    path("interests/", InterestListView.as_view(), name="interests"),
    path("save-interests/", SaveUserInterestsView.as_view(), name="save_interests"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

]
