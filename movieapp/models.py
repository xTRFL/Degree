from django.db import models




class MovieTitlesFinal(models.Model):
    movie_id = models.CharField(db_column='Movie_ID', max_length=20, primary_key=True)
    number = models.IntegerField(db_column='Number')
    ids = models.IntegerField(db_column='ID')
    type = models.CharField(db_column='Type', max_length=20)
    title = models.CharField(db_column='Title', max_length=200)
    org_title = models.CharField(db_column='Org_Title', max_length=200)
    adult = models.IntegerField(db_column='Adult')
    start_year = models.CharField(db_column='Start_Year', max_length=11)
    end_year = models.CharField(db_column='End_Year', max_length=11)
    runtime = models.IntegerField(db_column='Runtime')
    genres = models.CharField(db_column='Genres', max_length=100)

    class Meta:
        managed = True
        db_table = 'movie_titles_final'


class RatingsTitles(models.Model):
    id = models.AutoField(db_column = 'ID', primary_key=True)
    movie_id = models.CharField(db_column='Movie_ID', max_length=20)
    user_id = models.CharField(db_column='User_ID', max_length=20)
    rating = models.IntegerField(db_column='Rating')
    number = models.IntegerField(db_column='Number')
    type = models.CharField(db_column='Type', max_length=20)
    title = models.CharField(db_column='Title', max_length=200)
    org_title = models.CharField(db_column='Org_Title', max_length=200)
    adult = models.IntegerField(db_column='Adult')
    start_year = models.CharField(db_column='Start_Year', max_length=11)
    end_year = models.CharField(db_column='End_Year', max_length=11)
    runtime = models.IntegerField(db_column='Runtime')
    genres = models.CharField(db_column='Genres', max_length=100)

    class Meta:
        managed = True
        db_table = 'ratings_titles'

class UsersRecommendations(models.Model):
    user_id = models.CharField(db_column='User_ID', max_length=20, primary_key=True)
    recommendations_svd = models.CharField(db_column='Recommendations_svd', max_length=200)
    recommendations_rsvd = models.CharField(db_column='Recommendations_rsvd', max_length=200)
    recommendations_nosvd = models.CharField(db_column='Recommendations_nosvd', max_length=200)

    class Meta:
        managed = True
        db_table = 'users_recommendations'