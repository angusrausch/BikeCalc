from django.urls import path, include
from django.contrib import admin
from . import views, profile_views, fit_views

urlpatterns = [
    path("", views.index, name="index"),
    path('speed', views.speed, name="speed"),
    path('about', views.about_me, name="about_me"),
    path('rollout', views.rollout, name='rollout'),
    path('ratios', views.ratio, name='ratio'),
    path('feedback', views.feedback, name="feedback"),



    
    path("login", profile_views.login_view, name="login"),
    path("sign_up", profile_views.sign_up, name="sign_up"),

    path("profile", profile_views.profile, name="profile"),
    path("logout/<str:prevpage>/", profile_views.logout_view, name="logout"),
    path('table/<str:table_name>/', profile_views.table_view, name='table_view'),
    path('createblog', profile_views.create_blog, name='create_blog'),
    path('createbike', profile_views.create_bike, name="create_bike"),

    path('fittool', fit_views.fitviewer, name='fit-home')
]
