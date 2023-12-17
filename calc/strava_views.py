from django.http import HttpResponse
from django.template import loader
from django.http import Http404
from django.shortcuts import render, redirect
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from django.contrib.auth import login, authenticate
from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
import requests
from requests.exceptions import RetryError, HTTPError, RequestException
from mysecrets import CLIENT_SECRET_KEY, CLIENT_ID, MAPBOX_SECRET_KEY, GOOGLEMAPS_SECRET_KEY, CALLBACK_URL
from.fitter import powerCurveMaker
import time
import polyline
import math


def revoke_strava_token(request):
    # Specify the access token in the Authorization header
    access_token = request.session.get('access')
    headers = {'Authorization': f'Bearer {access_token}'}

    # Make a POST request to the deauthorization endpoint
    response = requests.post('https://www.strava.com/oauth/deauthorize', headers=headers)
    
    # Remove the 'access' key from the session data
    if 'access' in request.session:
        del request.session['access']

    if response.status_code == 200:
        print("Strava access token revoked successfully")
    else:
        print(f"Failed to revoke Strava access token. Status code: {response.status_code}")
        print(response.text)


def refresh_token(request):
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET_KEY
    refresh_token = request.session.get('refresh')
    token_url = "https://www.strava.com/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    }

    try:
        # Make a POST request to the token endpoint
        response = requests.post(token_url, data=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            token_data = response.json()

            # Extract the new access token and refresh token
            new_access_token = token_data['access_token']
            new_refresh_token = token_data.get('refresh_token', refresh_token)

            request.session['access'] = new_access_token
            request.session['expiry'] = response.json().get('expires_at')
            request.session['refresh'] = response.json().get('refresh_token')
            return
        else:
            # Handle the error case
            print(f"Token refresh failed with status code {response.status_code}")
            revoke_strava_token(request)
            print(response.text)
            

    except Exception as e:
        print(f"An error occurred during token refresh: {e}")

    revoke_strava_token(request)
    return redirect('strava-home')

def main_data(request, context):
    try:
        access_token = request.session.get('access')
        headers = {'Authorization': f'Bearer {access_token}'}


        response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        
        if response.status_code == 200:
            athlete_data = response.json()
        elif response.status_code == 429:
            raise RetryError(response=response)
        else:
            response.raise_for_status()
        

        response = requests.get(f'https://www.strava.com/api/v3/athletes/{athlete_data["id"]}/stats', headers=headers)

        if response.status_code == 200:
            athlete_data = athlete_data | response.json()
        elif response.status_code == 429:
            raise RetryError(response=response)       
        else:
            response.raise_for_status()
            

        response = requests.get('https://www.strava.com/api/v3/athlete/activities?per_page=100', headers=headers)
        
        if response.status_code == 200:
            athlete_activities = response.json()
        elif response.status_code == 429:
            raise RetryError(response=response)
        else:
            response.raise_for_status()


    except HTTPError as http_error:
        context['error'] = f"HTTP error: {http_error}"
        return render(request, 'calc/strava/main.html', context)
    except RetryError as retry_error:
        context['error'] = f"Rate limit exceeded: {retry_error}"
        return render(request, 'calc/strava/main.html', context)
    
    else:
        converted_data = {
            'id': athlete_data['id'],
            'firstname': athlete_data['firstname'],
            'lastname': athlete_data['lastname'],
            'city': athlete_data['city'],
            'state': athlete_data['state'],
            'country': athlete_data['country'],
            'premium': athlete_data['premium'],
            'weight': athlete_data['weight'],
            'profile_medium': athlete_data['profile_medium'],
            'follower_count': athlete_data['follower_count'],
            'friend_count': athlete_data['friend_count'],
            'clubs': athlete_data['clubs'],
            'ftp': athlete_data['ftp'],
            'bikes': athlete_data['bikes'],
            'biggest_ride_distance': athlete_data['biggest_ride_distance'] / 1000,
            'biggest_climb_elevation_gain': athlete_data['biggest_climb_elevation_gain'],
            'recent_ride_totals': {
                'count': athlete_data['recent_ride_totals']['count'],
                'distance': int(athlete_data['recent_ride_totals']['distance'] / 1000),
                'moving_time': int(athlete_data['recent_ride_totals']['moving_time'] / 3600),
                'elapsed_time': int(athlete_data['recent_ride_totals']['elapsed_time'] / 3600),
                'elevation_gain': athlete_data['recent_ride_totals']['elevation_gain'],
                'achievement_count': athlete_data['recent_ride_totals']['achievement_count']
            },
            'all_ride_totals': {
                'count': athlete_data['all_ride_totals']['count'],
                'distance': int(athlete_data['all_ride_totals']['distance'] / 1000),
                'moving_time': int(athlete_data['all_ride_totals']['moving_time'] / 3600),
                'elapsed_time': int(athlete_data['all_ride_totals']['elapsed_time'] / 3600),
                'elevation_gain': athlete_data['all_ride_totals']['elevation_gain']
            },
            'ytd_ride_totals': {
                'count': athlete_data['ytd_ride_totals']['count'],
                'distance': int(athlete_data['ytd_ride_totals']['distance'] / 1000),
                'moving_time': int(athlete_data['ytd_ride_totals']['moving_time'] / 3600),
                'elapsed_time': int(athlete_data['ytd_ride_totals']['elapsed_time'] / 3600),
                'elevation_gain': athlete_data['ytd_ride_totals']['elevation_gain']
            }
        }   
        for bike in range(len(athlete_data['bikes'])):
            athlete_data['bikes'][bike]['converted_distance'] = round(athlete_data['bikes'][bike]['converted_distance'])

        processed_athlete_activities = []
        for athlete_activity in athlete_activities:
            processed_athlete_activity = athlete_activity
            processed_athlete_activity['distance'] = int(processed_athlete_activity['distance'] / 1000)
            processed_athlete_activity['start_date_local'] = datetime.strptime(processed_athlete_activity['start_date_local'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
            processed_athlete_activities.append(processed_athlete_activity)
            
        request.session['athlete_data'] = converted_data
        request.session['athlete_activites'] = athlete_activities
        context['athlete'], context['activities'] = converted_data, athlete_activities
        # return render(request, 'calc/strava/logged-in.html', context)
        return redirect('strava-home') #Redirecting so a refresh of page doesn't request resources again
    

@csrf_protect
def main(request):
    context = {
        'page': 'strava-home',
        'url': CALLBACK_URL
    }

    if request.user.is_authenticated: 

        if 'access' in request.session:
            #If access has already been granted
            access_token = request.session.get('access')
            if time.time() >= request.session.get('expiry') - 3600:
                refresh_token(request)
                return main_data(request, context)
            
            if request.method == "POST":
                data = request.POST

                if data.get('logout') == "1":
                    revoke_strava_token(request)
                    keys_to_clear = ['access', 'token_type', 'expiry', 'refresh', 'athlete', 'athlete_data', 'athlete_activites']
                    for key in keys_to_clear:
                        if key in request.session:
                            del request.session[key]
                    return render(request, 'calc/strava/main.html', context)
                
                elif data.get('refresh') == "1":
                    return main_data(request, context)
                
                
            converted_data = request.session.get('athlete_data')
            athlete_activities = request.session.get('athlete_activites')

            context['athlete'], context['activities'] = converted_data, athlete_activities
            return render(request, 'calc/strava/logged-in.html', context)
        
            
        elif 'code' in request.GET:
            #If user has logged in
            try:
                authorization_code = request.GET['code']

                client_id = CLIENT_ID
                client_secret = CLIENT_SECRET_KEY
                redirect_uri = CALLBACK_URL  
                token_url = 'https://www.strava.com/oauth/token'

                data = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': authorization_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                }

                response = requests.post(token_url, data=data)

                if response.status_code == 200:
                    access_token = response.json().get('access_token')
                    request.session['access'] = access_token
                    request.session['token_type'] = response.json().get('token_type')
                    request.session['expiry'] = response.json().get('expires_at')
                    request.session['refresh'] = response.json().get('refresh_token')
                    request.session['athlete'] = response.json().get('athlete')
    
                else:
                    if 'access' in request.session:
                        del request.session['access']
                    error_message = response.json().get('error_description', 'Token exchange failed')
                    response = requests.post(token_url, data=data)
                    raise RequestException((response, error_message))
            except RequestException as requesterror:
                
                context['error'] = str(requesterror)
                return render(request, 'calc/strava/main.html', context)
            except RetryError as retry_error:
                context['error'] = f"Rate limit exceeded: {retry_error}"
                return render(request, 'calc/strava/main.html', context)
            else:
                return main_data(request, context)
            
        
        return render(request, 'calc/strava/main.html', context)
        
        
    else:
        return redirect('login')
    

@csrf_protect
def activity(request, activity_id):
    context = {'page': 'strava-home'}
    if request.user.is_authenticated:
        if 'access' in request.session:
            try:

                if time.time() >= request.session.get('expiry') - 3600:
                    refresh_token(request)
                
                access_token = request.session.get('access')
                headers = {'Authorization': f'Bearer {access_token}'}


                response = requests.get(f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=false", headers=headers)

                if response.status_code == 200:
                    activity_data = response.json()
                elif response.status_code == 429:
                    raise RetryError(response=response)
                else:
                    response.raise_for_status()

                # # activity file
                # print("TEST")
                # headers = {'Authorization': f'Bearer {access_token}'}
                # response = requests.get(f"https://www.strava.com/api/v3/activities/{activity_id}/streams?keys=time,watts,heartrate,cadence,grade_smooth&key_by_type=false", headers=headers)
                # if response.status_code == 200:
                #     file = response.json()
                #     # for key, value in file.items():
                #     #     print(f"{key}: {value}")
                #     #     pass

                #     if 'watts' in file:
                #         print(file['watts']) 
                #         print("POWER")
                #         print(type(file['watts']['data']))
                #         power_curve = powerCurveMaker(file['watts']['data'])
                #         print(power_curve[3600])
                # elif response.status_code == 429:
                #     raise RetryError(response=response)
                # else:
                #     response.raise_for_status()
                # print("ENDTEST")
                # # activity file
                

            except HTTPError as http_error:
                if http_error.response.status_code == 404:
                    context['error'] = "Activity not found. This may be because it is another athletes activity"
                else:
                    context['error'] = f"HTTP error: {http_error}"
                return render(request, 'calc/strava/main.html', context)
            
            except RetryError as retry_error:
                context['error'] = f"Rate limit exceeded: {retry_error}"
                return render(request, 'calc/strava/main.html', context)
            else:
                activity_data['distance'] = round(activity_data['distance']/1000, 2)
                activity_data['start_date'] = datetime.strptime(activity_data['start_date_local'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
                activity_data['start_time'] = datetime.strptime(activity_data['start_date_local'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
                activity_data['moving_time'] = f"{int(int(activity_data['moving_time'])/3600):02d}:{int(activity_data['moving_time']%3600/60):02d}"
                activity_data['elapsed_time'] = f"{int(int(activity_data['elapsed_time'])/3600):02d}:{int(activity_data['elapsed_time']%3600/60):02d}"
                activity_data['average_speed'] = round(activity_data['average_speed']*3.6, 1)
                activity_data['max_speed'] = round(activity_data['max_speed']*3.6, 1)
                encoded_polyline =  polyline.decode(activity_data['map']['polyline'], 5)
                points = []
                for point in encoded_polyline:
                    points.append([point[0], point[1]])
                
                context = context | {
                    'activity': activity_data,
                    'secret': {'mapbox': MAPBOX_SECRET_KEY, 'google': GOOGLEMAPS_SECRET_KEY},
                    'polyline': points,
                }
                return render(request, 'calc/strava/activity.html', context)
            
        else: return redirect('strava-home')
            
    else: return redirect('login')


@csrf_protect
def bike(request, bike_id):
    context = {'page': 'strava-home'}
    if request.user.is_authenticated:
        if 'access' in request.session:

            try:
                if time.time() >= request.session.get('expiry') - 3600:
                    refresh_token(request)




                access_token = request.session.get('access')
                headers = {'Authorization': f'Bearer {access_token}'}
                response = requests.get(f"https://www.strava.com/api/v3/gear/{bike_id}", headers=headers)

                if response.status_code == 200:
                    bike_data = response.json()
                elif response.status_code == 429:
                    raise RetryError(response=response)
                else:
                    response.raise_for_status()

            except HTTPError as http_error:
                if http_error.response.status_code == 404:
                    context['error'] = "Activity not found. This may be because it is another athletes activity"
                else:
                    context['error'] = f"HTTP error: {http_error}"
                return render(request, 'calc/strava/main.html', context)
            except RetryError as retry_error:
                context['error'] = f"Rate limit exceeded: {retry_error}"
                return render(request, 'calc/strava/main.html', context)
            else:


                context = context | {
                    'bike': bike_data
                    
                }



                # response = requests.get(f"https://www.strava.com/api/v3/routes/3128270842261936740", headers=headers)
                # raw = response.json()
                # segments = raw['segments']
                # raw['segments'] = ""
                # for key, value in raw.items():
                #     print(f"{key}: {value}\n")
                # for segment in segments:
                #     print(segment, "\n")
                

                
                return render(request, 'calc/strava/bike.html', context)
            
        else: return redirect('strava-home')
            
    else: return redirect('login')


