# Generated by Django 4.1.6 on 2023-06-18 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movieapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersrecommendations',
            name='id',
        ),
        migrations.AlterField(
            model_name='usersrecommendations',
            name='user_id',
            field=models.CharField(db_column='User_ID', max_length=20, primary_key=True, serialize=False),
        ),
    ]