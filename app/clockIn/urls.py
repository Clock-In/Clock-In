"""
URL configuration for clockIn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from base import views
from django.contrib.auth import views as auth_views

auth_urls = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout, name="logout"),
    path(
        "password_change/", auth_views.PasswordChangeView.as_view(), name="password_change"
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("password_reset/", auth_views.PasswordResetView.as_view(), # TODO: set up smtp config 
         name="password_reset"),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path('profile/', views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
]

statistic_urls = [
    path("", views.earnings, name="statistics"),
    path("distribution", views.distribution, name="distribution"),
    path("history/<str:period>", views.history, name="history"),
    path("earnings", views.earnings, name="earnings"),
    path("insights", views.insights, name="insights"),
    path("breakdown", views.breakdown, name="breakdown"),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(auth_urls)),
    path('timetable/', views.timetable_month, name="timetable"),
    path('timetable/week/', views.timetable_week, name="timetable_week"),
    path('timetable/create/', views.create_timetable, name="create_timetable"),
    path('my_shift/<str:pk>/', views.my_shift, name="my_shift"),
    path('statistics/', include(statistic_urls)),
    path('shift/<str:pk>/swap/', views.shift_swap_request, name="swap_request"),
    path('shift/available/', views.view_shift_requests, name="view_requests"),
    path('shift/<int:pk>/delete/', views.delete_shift, name='delete_shift'),
    path('shift/<int:pk>/edit/', views.edit_shift, name='edit_shift'),
]


