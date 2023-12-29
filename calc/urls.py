from django.urls import path, include
from django.contrib import admin
from . import views, profile_views, fit_views, strava_views, map_views

urlpatterns = [
    path('get-google-maps-key/', views.get_google_maps_key, name='get-google-maps-key'),

    #Main
    path("", views.index, name="index"),
    path('speed', views.speed, name="speed"),
    path('about', views.about_me, name="about_me"),
    path('rollout', views.rollout, name='rollout'),
    path('ratios', views.ratio, name='ratio'),
    path('feedback', views.feedback, name="feedback"),

    #Profile
    path("login", profile_views.login_view, name="login"),
    path("sign_up", profile_views.sign_up, name="sign_up"),
    path("profile", profile_views.profile, name="profile"),
    path("logout/<str:prevpage>/", profile_views.logout_view, name="logout"),
    path('table/<str:table_name>/', profile_views.table_view, name='table_view'),
    path('edittable/<str:table_name>/<int:id>/', profile_views.edittable_view, name='edittable_view'),
    path('createblog', profile_views.create_blog, name='create_blog'),

    #Fit File Viewer
    path('fittool', fit_views.fitviewer, name='fit-home'),

    #Strava
    path('strava', strava_views.main, name='strava-home'),
    path('strava/activity/<int:activity_id>/', strava_views.activity, name='activity'),
    path('strava/bike/<str:bike_id>/', strava_views.bike, name='bike'),
    path('strava/segments', strava_views.segments, name = 'segments'),
    path('strava/segments/<int:id>', strava_views.segments, name = 'segments'),

    #Maps
    path('racks', map_views.racks, name='racks'),
]
