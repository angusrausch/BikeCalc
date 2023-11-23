from django import forms
from .models import Wheel_size, Tyre_Size, bike,Cassette,Chainrings

class SpeedForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ('wheel', 'tyre', 'chainring', 'cassette', 'cadence')
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['wheel'].queryset = Wheel_size.objects.none()