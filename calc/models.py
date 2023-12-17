from django.db import models
from django.contrib.auth.models import User


class Cassettes(models.Model):
    cassette_name = models.CharField(max_length=20, null=True)
    speeds = models.IntegerField()
    sprockets = models.CharField(max_length=64)
    user_generated = models.BooleanField()

    def __str__ (self):
        return self.cassette_name
    
class Chainrings(models.Model):
    chainring_name = models.CharField(max_length=16, null=True)
    large = models.IntegerField()
    middle = models.IntegerField(null=True)
    small = models.IntegerField(null=True)
    user_generated = models.BooleanField()
    def __str__ (self):
        return self.chainring_name

class Tyre_Size(models.Model):
    tyre_size_name = models.CharField(max_length=50)
    tyre_circumference = models.IntegerField()
    def __str__ (self):
        return self.tyre_size_name
    
class Bike (models.Model):
    bike_name = models.CharField(max_length=64)
    Chainring = models.ForeignKey(Chainrings, on_delete=models.CASCADE)
    Cassette = models.ForeignKey(Cassettes, on_delete=models.CASCADE)
    tyre = models.ForeignKey(Tyre_Size, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__ (self):
        return self.bike_name
    
class Blog (models.Model):
    title = models.CharField(max_length=128)
    body = models.CharField(max_length=2048)
    date_field = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class user_feedback (models.Model):
    title = models.CharField(max_length=128)
    contact = models.CharField(max_length=128)
    body = models.CharField(max_length=2048)
    date = models.DateField()
  
