# Generated by Django 4.2.7 on 2023-11-11 12:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0012_rename_feedback_body_feedback_body_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='feedback',
            new_name='user_feedback',
        ),
    ]
