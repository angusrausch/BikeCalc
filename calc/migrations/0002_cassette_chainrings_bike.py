# Generated by Django 4.2.7 on 2023-11-09 05:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cassette',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cassette_name', models.CharField(max_length=10)),
                ('speeds', models.IntegerField()),
                ('sprockets', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Chainrings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chainring_name', models.CharField(max_length=10)),
                ('large', models.IntegerField()),
                ('middle', models.IntegerField(null=True)),
                ('small', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Bike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bike_name', models.CharField(max_length=100)),
                ('Cassette', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.cassette')),
                ('Chainring', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.chainrings')),
                ('tyre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.tyre_size')),
            ],
        ),
    ]
