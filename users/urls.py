from django.urls import path
from .views import RegisterView, LoginView, HomeView, UsersListView, RequestResetPasswordView, InterestListView, \
    SaveUserInterestsView, UserProfileView, ChangePasswordView, ResetPasswordView, UpdateAccountTypeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('home/', HomeView.as_view(), name='home'),
    path("users/", UsersListView.as_view(), name="users_list"),
    path("users/<uuid:pk>/update-account-type/",
         UpdateAccountTypeView.as_view(), name="update_account_type"),
    path("interests/", InterestListView.as_view(), name="interests"),
    path("save-interests/", SaveUserInterestsView.as_view(), name="save_interests"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("forget-password/", RequestResetPasswordView.as_view(),
         name="forget_password"),
    path("reset-password/<str:token>",
         ResetPasswordView.as_view(), name="reset_password"),
]
