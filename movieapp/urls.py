from django.urls import path

from . import views
from .views import SignUpView

urlpatterns = [
    path("", views.index, name="index"),
    path("movies/", views.movies_list, name="movies"),
    path("recommendation/", views.recommendation, name="recommendation"),
    path("user/", views.user_details, name="user"),
    path("userSVD/", views.userSVD, name="SVD"),
    path("userRSVD/", views.userRSVD, name="RSVD"),
    path("userNOSVD/", views.userNOSVD, name="NoSVD"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("<str:movie_id>/", views.detail, name="detail"),
    path("rate/<str:movieID>", views.movie_ratings, name='rating'),
    path('poster/<str:imdb_id>/', views.movie_poster, name='poster'),
]