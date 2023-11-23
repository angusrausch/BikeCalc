from django.contrib import admin

from .models import Tyre_Size, Chainrings, Cassettes, Bike, Blog, user_feedback

admin.site.register(Tyre_Size)
admin.site.register(Cassettes)
admin.site.register(Chainrings)
admin.site.register(Bike)
admin.site.register(Blog)
admin.site.register(user_feedback)
# Register your models here.
