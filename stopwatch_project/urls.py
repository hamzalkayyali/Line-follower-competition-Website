# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    # Page routes
    path('', views.leaderboard_page, name='leaderboard'),
    path('display/', views.display_page, name='display'),
    path('judge/', views.judge_page, name='judge'),
    path('judge/login/', views.judge_login, name='judge_login'),
    path('judge/logout/', views.judge_logout, name='judge_logout'),

    # Calibration API (must be before the generic trigger route)
    path('api/calibration/state/', views.api_calibration_state, name='api_calibration_state'),
    path('api/calibration/start/', views.api_calibration_start, name='api_calibration_start'),
    path('api/calibration/pause/', views.api_calibration_pause, name='api_calibration_pause'),
    path('api/calibration/reset/', views.api_calibration_reset, name='api_calibration_reset'),
    path('api/calibration/set-teams/', views.api_calibration_set_teams, name='api_calibration_set_teams'),

    # API — Stopwatch state (ESP32 integration)
    path('api/state/', views.get_state, name='get_state'),
    path('api/<str:track>/<str:action>/', views.trigger_event, name='trigger_event'),

    # API — Data endpoints
    path('api/teams/', views.api_teams, name='api_teams'),
    path('api/leaderboard/', views.api_leaderboard, name='api_leaderboard'),
    path('api/submit-run/', views.api_submit_run, name='api_submit_run'),
    path('api/delete-run/', views.api_delete_run, name='api_delete_run'),
    path('api/active-run/', views.api_active_run, name='api_active_run'),
    path('api/set-active-run/', views.api_set_active_run, name='api_set_active_run'),
    path('api/clear-active-run/', views.api_clear_active_run, name='api_clear_active_run'),
    path('api/add-team/', views.api_add_team, name='api_add_team'),
    path('api/edit-team/', views.api_edit_team, name='api_edit_team'),
    path('api/delete-team/', views.api_delete_team, name='api_delete_team'),

    # Calibration pages
    path('calibration/', views.calibration_display, name='calibration_display'),
    path('calibration/control/', views.calibration_control, name='calibration_control'),
    path('calibration/login/', views.calibration_login, name='calibration_login'),
    path('calibration/logout/', views.calibration_logout, name='calibration_logout'),

]