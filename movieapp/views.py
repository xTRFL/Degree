from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.db.models.functions import Random

from .forms import NewUserForm
from django.contrib.auth import login
from django.contrib.auth.decorators import *
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from math import sqrt
import pandas as pd
import random
import numpy as np
import requests
import tmdbsimple
from scipy.linalg import svd
from sklearn.metrics import mean_squared_error
from sklearn.utils.extmath import randomized_svd
from scipy.sparse.linalg import svds
from scipy.spatial.distance import euclidean

from .models import *

tmdbsimple.API_KEY = "3ae793eef198e298de1fbe9969107df4"

def index(request):
    return render(request, 'home.html')

def detail(request, movie_id):
    rating_exists = RatingsTitles.objects.filter(movie_id = movie_id, user_id = request.user.id)
    rating_list = rating_exists.values()
    if len(rating_list) > 0:
        rating_exists.delete()
    try:
        movie = MovieTitlesFinal.objects.get(pk=movie_id)
    except MovieTitlesFinal.DoesNotExist:
        raise Http404("Movie does not exist")
    try:
        rating = int(RatingsTitles.objects.get(movie_id = movie_id, user_id = request.user.id).rating)
    except RatingsTitles.DoesNotExist:
        rating = 0
    return render(request, "movieapp/detail.html", {"movie": movie, "rating" : rating})

@cache_page(60 * 15)
def movies_list(request):
    movies = MovieTitlesFinal.objects.all()

    movies_per_page = 20
    paginator = Paginator(movies, movies_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'movieapp/movies_list.html', { 'page': page})

@cache_page(60 * 15)
def movie_poster(request, imdb_id):
    search = tmdbsimple.Find(imdb_id)
    search_info = search.info(external_source='imdb_id')

    poster_path = search_info['movie_results'][0]['poster_path'] if search_info['movie_results'] else None

    if poster_path:
        response = requests.get(f'https://image.tmdb.org/t/p/w500/{poster_path}')
        content_type = response.headers['Content-Type']
    
        return HttpResponse(content=response.content, content_type=content_type)

    response = requests.get(f"https://via.placeholder.com/300x450.png")
    return HttpResponse(content=response.content, content_type='image/jpeg')


def movie_ratings(request, movieID):
  rating_exists = RatingsTitles.objects.filter(movie_id = movieID, user_id = request.user.id)
  rating_list = rating_exists.values()
  if len(rating_list) > 0:
    rating_exists.delete()
  if request.method == 'POST':
    rating_value = int(request.POST.get('rating'))
    movie_details = MovieTitlesFinal.objects.filter(movie_id = movieID).values()[0]
    max_id = RatingsTitles.objects.filter().order_by('-id')[0]
    rating = RatingsTitles(user_id=request.user.id, movie_id = movieID, rating=rating_value, number = 0, id = int(max_id.id) + 1, type = movie_details['type'],
                           title = movie_details['title'], org_title = movie_details['org_title'], adult = movie_details['adult'],
                           start_year = movie_details['start_year'], end_year = movie_details['end_year'], runtime = movie_details['runtime'], genres = movie_details['genres'])
    rating.save()
  return render(request, 'movieapp/detail.html', {'movie': rating, 'rating': int(rating.rating)})


def admin_check(user):
   return user.is_superuser

def recommendations_SVD(userID):
    k = 10000
    rates = list(RatingsTitles.objects.filter(user_id = userID).values_list("user_id", "movie_id", "rating"))
    if len(rates) < 10:
        return {}
    table2 = RatingsTitles.objects.filter(user_id__gt = userID).values_list("user_id", "movie_id", "rating").order_by('user_id')
    if len(table2) > k:
        table2 = list(table2)
        begin = random.randint(0, len(table2)-(k + 1))
        table2 = table2[begin:begin+k]
        table2 = rates + table2
    else:
        table2 = RatingsTitles.objects.filter(user_id__lt = userID).values_list("user_id", "movie_id", "rating").order_by('-user_id')
        table2 = list(table2)
        begin = random.randint(0, len(table2)-(k+1))
        table2 = table2[begin:begin+k]
        table2 = rates + table2
    table2 = pd.DataFrame(table2, columns=["User_ID", "Movie_ID", "Rating"])
    
    table2 = pd.pivot_table(table2, index='User_ID', columns="Movie_ID", values="Rating")
    table2 = table2.fillna(-1)
    tab1, tab2, tab3 = svd(table2)
    tab22 = np.diag(tab2)
    tab22.resize((tab1.shape[0], tab3.shape[1]), refcheck=False)
    tab4 = np.array(tab1[4])
    tab5 = tab4@tab22
    tab3 = np.array(tab3)
    tab3.resize((tab5.shape[0], tab3.shape[1]), refcheck=False)
    predicted_ratings = tab5@tab3

    index_sort = sorted(range(len(predicted_ratings)), key=lambda k: predicted_ratings[k], reverse=True)

    temp = []
    for i in range(len(predicted_ratings)):
        if list(table2.values)[0][index_sort[i]] == -1:
            temp.append(list(table2)[i])
            if(len(temp) > 15):
                break
    temp2 = []
    for id in temp:
        temp2.append(MovieTitlesFinal.objects.filter(movie_id = id))
    return {'movies': temp2, 'MSE': sqrt(mean_squared_error(list(table2.values)[0], list(predicted_ratings)))}

def calculate_new_dimension(table):
    _, x, _ = svds(table.values, k=min(table.shape[1], table.shape[0])-1)
    sorted_values = np.sort(x)[::-1]

    temp_sum = np.sum(sorted_values)

    temp_sum2 = np.cumsum(sorted_values)
    ratio = temp_sum2 / temp_sum

    dim = np.argmax(ratio >= 0.8)
    dim = dim + 1

    return dim

def recommendations_RSVD(userID):
    k = 10000
    rates = list(RatingsTitles.objects.filter(user_id = userID).values_list("user_id", "movie_id", "rating"))
    if len(rates) < 10:
        return {}
    table2 = RatingsTitles.objects.filter(user_id__gt = userID).values_list("user_id", "movie_id", "rating").order_by('user_id')
    if len(table2) > k:
        table2 = list(table2)
        begin = random.randint(0, len(table2)-(k+1))
        table2 = table2[begin:begin+k]
        table2 = rates + table2
    else:
        table2 = RatingsTitles.objects.filter(user_id__lt = userID).values_list("user_id", "movie_id", "rating").order_by('-user_id')
        table2 = list(table2)
        begin = random.randint(0, len(table2)-(k+1))
        table2 = table2[begin:begin+k]
        table2 = rates + table2

    table2 = pd.DataFrame(table2, columns=["User_ID", "Movie_ID", "Rating"])
    
    table2 = pd.pivot_table(table2, index='User_ID', columns="Movie_ID", values="Rating")
    table2 = table2.replace([np.inf, -np.inf], np.nan)
    table2 = table2.fillna(-1)
    a,b,c = randomized_svd(table2, n_components=calculate_new_dimension(table2)) #Randomized_SVD
    b2 = np.diag(b)
    d = np.array(a[0])

    e = d@b2
    predicted_ratings = e@c

    index_sort = sorted(range(len(predicted_ratings)), key=lambda k: predicted_ratings[k], reverse=True)

    temp = []
    for i in range(len(predicted_ratings)):
        if list(table2.values)[0][index_sort[i]] == -1:
            temp.append(list(table2)[i])
            if(len(temp) > 15):
                break
    temp2 = []
    for id in temp:
        temp2.append(MovieTitlesFinal.objects.filter(movie_id = id))
    print(len(list(table2.values)[0]), len(list(predicted_ratings)))
    return {'movies': temp2, 'MSE': sqrt(mean_squared_error(list(table2.values)[0], list(predicted_ratings)))}

def recommendations_euclidean(userID):
    k = 10000
    rates = list(RatingsTitles.objects.filter(user_id = userID).values_list("user_id", "movie_id", "rating"))
    if len(rates) < 10:
        return {} 
    table2 = RatingsTitles.objects.filter(user_id__gt = userID).values_list("user_id", "movie_id", "rating").order_by('user_id')
    if len(table2) > k:
        table2 = list(table2)
        begin = random.randint(0, len(table2)-(k+1))
        table2 = table2[begin:begin+k]
        table2 = rates + table2
    else:
        table2 = RatingsTitles.objects.filter(user_id__lt = userID).values_list("user_id", "movie_id", "rating").order_by('-user_id')
        table2 = list(table2)
        begin = random.randint(0, len(table2)-(k+1))
        table2 = table2[begin:begin+k]
        table2 = rates + table2
    table2 = pd.DataFrame(table2, columns=["User_ID", "Movie_ID", "Rating"])
    table2 = pd.pivot_table(table2, index='User_ID', columns="Movie_ID", values="Rating")
    table2 = table2.fillna(-1)

    user = list(table2.values)[0]
    distances = []
    for other_user in list(table2.values)[1:]:
        distance = euclidean(user, other_user)
        distance = 1/(distance+1)
        distances.append(distance)
    closest_user = np.argmin(distances)
    predicted_ratings = list(table2.values)[closest_user]

    temp = []
    for i in range(len(predicted_ratings)):
        if user[i] == -1 and predicted_ratings[i] > -1:
            temp.append(list(table2)[i])
        if(len(temp) > 15):
            break

    temp2 = []
    for id in temp:
        temp2.append(MovieTitlesFinal.objects.filter(movie_id = id))
    
    if len(temp) < 1:
        return recommendations_euclidean(userID)

    return {'movies': temp2, 'MSE': mean_squared_error(list(table2.values)[0], list(predicted_ratings))}

@login_required
@csrf_exempt
def userSVD(request):
    user_id = request.user.id
    recommendations = recommendations_SVD(user_id)
    recommendations_ids = []
    for x in recommendations['movies']:
        recommendations_ids.append(str(x[0].movie_id))
    if len(recommendations) < 1:
        return render(request, 'movieapp/error.html')
    save_recommendations(request, recommendations_ids, 'svd')
    return render(request, 'movieapp/recommendationsSVD.html', recommendations)

@login_required
@csrf_exempt
def userRSVD(request):
    user_id = request.user.id
    recommendations = recommendations_RSVD(user_id)
    recommendations_ids = []
    for x in recommendations['movies']:
        recommendations_ids.append(str(x[0].movie_id))
    if len(recommendations) < 1:
        return render(request, 'movieapp/error.html')
    save_recommendations(request, recommendations_ids, 'rsvd')
    return render(request, 'movieapp/recommendationsSVD.html', recommendations)

@login_required
@csrf_exempt
def userNOSVD(request):
    user_id = request.user.id
    recommendations = recommendations_euclidean(user_id)
    recommendations_ids = []
    for x in recommendations['movies']:
        recommendations_ids.append(str(x[0].movie_id))
    if len(recommendations) < 1:
        return render(request, 'movieapp/error.html')
    save_recommendations(request, recommendations_ids, 'nosvd')
    return render(request, 'movieapp/recommendationsSVD.html', recommendations)

def save_recommendations(request, recommendations, svd_type):
    reco_str = ','.join(recommendations)
    try:
        svd = UsersRecommendations.objects.get(user_id = request.user.id)
    except UsersRecommendations.DoesNotExist:
        if svd_type == 'svd':
            recommendation = UsersRecommendations(user_id = request.user.id, recommendations_svd = reco_str, recommendations_rsvd = '', recommendations_nosvd = '')
        if svd_type == 'rsvd':
            recommendation = UsersRecommendations(user_id = request.user.id, recommendations_svd = '', recommendations_rsvd = reco_str, recommendations_nosvd = '')
        if svd_type == 'nosvd':
            recommendation = UsersRecommendations(user_id = request.user.id, recommendations_svd = '', recommendations_rsvd = '', recommendations_nosvd = reco_str)
        recommendation.save()
        return
    
    if svd_type == 'svd':
        recommendation = UsersRecommendations(user_id = request.user.id, recommendations_svd = reco_str, recommendations_rsvd = svd.recommendations_rsvd, 
                                              recommendations_nosvd = svd.recommendations_nosvd)
    if svd_type == 'rsvd':
        recommendation = UsersRecommendations(user_id = request.user.id, recommendations_svd = svd.recommendations_svd, recommendations_rsvd = reco_str,
                                               recommendations_nosvd = svd.recommendations_nosvd)
    if svd_type == 'nosvd':
        recommendation = UsersRecommendations(user_id = request.user.id, recommendations_svd = svd.recommendations_svd, recommendations_rsvd = svd.recommendations_rsvd, 
                                              recommendations_nosvd = reco_str)
    recommendation.save()
    return

def recommendation(request):
    try:
        svd = UsersRecommendations.objects.get(user_id = request.user.id).recommendations_svd
    except UsersRecommendations.DoesNotExist:
        svd = ''
    if len(svd) > 1:
        svd = [MovieTitlesFinal.objects.get(movie_id = id) for id in svd.split(',')]
    try:
        rsvd = UsersRecommendations.objects.get(user_id = request.user.id).recommendations_rsvd
    except UsersRecommendations.DoesNotExist:
        rsvd = ''
    if len(rsvd) > 1:
        rsvd = [MovieTitlesFinal.objects.get(movie_id = id) for id in rsvd.split(',')]
    try:
        nosvd = UsersRecommendations.objects.get(user_id = request.user.id).recommendations_nosvd
    except UsersRecommendations.DoesNotExist:
        nosvd = ''
    if len(nosvd) > 1:
        nosvd = [MovieTitlesFinal.objects.get(movie_id = id) for id in nosvd.split(',')]
    return render(request, 'movieapp/recommendation.html', {'svd': svd, 'rsvd': rsvd, 'nosvd': nosvd})

def user_details(request):
    rates = RatingsTitles.objects.filter(user_id = request.user.id).values()
    return render(request, 'movieapp/user.html', {"rated" : rates})

class SignUpView(generic.CreateView):
    form_class = NewUserForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


