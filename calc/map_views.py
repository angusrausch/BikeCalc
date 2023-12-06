from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
import requests
from requests.exceptions import RetryError, HTTPError, RequestException
import os
from mysecrets import MAPBOX_SECRET_KEY, GOOGLEMAPS_SECRET_KEY

@csrf_protect
def racks(request):
    context = {
        'page': 'map-home',
        'google_maps_key': GOOGLEMAPS_SECRET_KEY,
    }

    # if request.user.is_authenticated:
    try:
        response = requests.get('https://www.data.brisbane.qld.gov.au/data/api/3/action/datastore_search?resource_id=4a67a16d-ffc7-4831-a77b-64d8ac42459e&limit=1000')

        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                rack_locations = data['result']['records']
            else:
                raise Exception(data)
        elif response.status_code == 429:
            raise RetryError(response=response)
        else:
            response.raise_for_status()


        
        response = requests.get('https://www.data.brisbane.qld.gov.au/data/api/3/action/datastore_search?resource_id=57b9ba99-16ea-4eb5-b21b-049c8f880377&limit=500')

        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                tap_locations = data['result']['records']
                # for item in tap_locations:
                #     print(item)
            else:
                raise Exception(data)

        elif response.status_code == 429:
            raise RetryError(response=response)
        else:
            response.raise_for_status()



    except requests.exceptions.RequestException as e:
        print("ERROR: ", e)
    else:
        context['racks'], context['taps'] = rack_locations, tap_locations
        # print(rack_locations)
        return render(request, 'calc/data/rack_locations.html', context)
    # else:
    #     return redirect('login')
