# Generated by Django 4.2.7 on 2023-11-14 10:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0015_delete_users_blog_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blog',
            name='about_me',
        ),
    ]