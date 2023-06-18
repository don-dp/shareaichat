from django.urls import path
from .views import AboutPage, SignupView, ProfileView, CustomPasswordResetView, CustomLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("about/", AboutPage.as_view(), name="aboutpage"),
    path("login/", CustomLoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset_done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password_reset_confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password_reset_complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path('signup/', SignupView.as_view(), name='signup'),
    path("password_change/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("password_change_done/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path('profile/', ProfileView.as_view(), name='profile'),
]