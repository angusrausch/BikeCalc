# Generated by Django 4.2.7 on 2023-11-11 12:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0011_rename_body_feedback_feedback_body_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='feedback',
            old_name='feedback_body',
            new_name='body',
        ),
        migrations.RenameField(
            model_name='feedback',
            old_name='feedback_contact',
            new_name='contact',
        ),
        migrations.RenameField(
            model_name='feedback',
            old_name='feedback_title',
            new_name='title',
        ),
    ]
