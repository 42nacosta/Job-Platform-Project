from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home.index'),
    path('about/', views.about, name='home.about'),
    path('<int:id>/', views.show, name='home.show'),
    path('<int:id>/apply/', views.apply_job, name='home.apply'),
    path('create/', views.create_job, name='home.create'),
    path('<int:id>/edit/', views.edit_job, name='home.edit'),
    path("candidates/", views.candidates, name="home.candidates"),
]
