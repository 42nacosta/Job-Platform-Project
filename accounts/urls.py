from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("privacy/", views.privacy_settings, name="privacy"),
    path("u/<str:username>/", views.profile_detail, name="profile"),
    path('signup', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
]