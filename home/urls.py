from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home.index'),
    path('about/', views.about, name='home.about'),
    path('<int:id>/', views.show, name='home.show'),
    path('<int:id>/apply/', views.apply_job, name='home.apply'),
    path('<int:id>/move/', views.move_app, name='home.move_app'),
    path('apps/', views.view_apps, name='home.apps'),
    path('create/', views.create_job, name='home.create'),
    path('<int:id>/edit/', views.edit_job, name='home.edit'),
    path("candidates/", views.candidates, name="home.candidates"),
    # Recommendation URLs
    path('jobs/<int:job_id>/recommended-candidates/', views.recruiter_recommendations, name='home.recruiter_recs'),
    path('recommendations/candidates/<int:rec_id>/dismiss/', views.dismiss_candidate_recommendation, name='home.dismiss_candidate'),
    path('recommended-jobs/', views.job_recommendations, name='home.job_recs'),
    path('recommendations/jobs/<int:rec_id>/dismiss/', views.dismiss_job_recommendation, name='home.dismiss_job'),
]
