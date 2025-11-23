from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home.index'),
    path('about/', views.about, name='home.about'),
    path('<int:id>/', views.show, name='home.show'),
    path('<int:id>/apply/', views.apply_job, name='home.apply'),
    path('<int:id>/move/', views.move_app, name='home.move_app'),
    path('apps/', views.apps, name='home.apps'),
    path('create/', views.create_job, name='home.create'),
    path('<int:id>/edit/', views.edit_job, name='home.edit'),
    path("candidates/", views.candidates, name="home.candidates"),
    # Pipeline URLs
    path("recruiting/pipeline/", views.pipeline_board, name="pipeline-board"),
    path("recruiting/pipeline/<int:job_id>/", views.pipeline_board, name="pipeline-board-job"),
    path("recruiting/pipeline/update/", views.pipeline_update_status, name="pipeline-update"),
    # Recommendation URLs
    path('jobs/<int:job_id>/recommended-candidates/', views.recruiter_recommendations, name='home.recruiter_recs'),
    path('recommendations/candidates/<int:rec_id>/dismiss/', views.dismiss_candidate_recommendation, name='home.dismiss_candidate'),
    path('recommended-jobs/', views.job_recommendations, name='home.job_recs'),
    path('recommendations/jobs/<int:rec_id>/dismiss/', views.dismiss_job_recommendation, name='home.dismiss_job'),
    # Saved Search URLs
    path("saved-searches/", views.saved_search_list, name="saved_search_list"),
    path("saved-searches/new", views.saved_search_create, name="saved_search_create"),
    path("saved-searches/<int:pk>/toggle", views.saved_search_toggle, name="saved_search_toggle"),
    path("saved-searches/<int:pk>/matches", views.saved_search_matches, name="saved_search_matches"),
    path("notifications/unread-count", views.saved_search_unread_count, name="saved_search_unread_count"),
    path("notifications/mark-seen", views.saved_search_mark_seen, name="saved_search_mark_seen"),
    path('job_map/', views.job_map, name='home.job_map'),
    path('api/map_data_api/', views.map_data_api, name='home.map_data_api'),
    # map clustering URLs
    path('recruiter/applicant-map/', views.applicant_map, name='home.applicant_map'),
    path('api/applicant_map_data/', views.applicant_map_data_api, name='home.applicant_map_data'),
]
