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
from mysecrets import CLIENT_SECRET_KEY, CLIENT_ID, MAPBOX_SECRET_KEY, GOOGLEMAPS_SECRET_KEY
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
    # Set up the data for the token refresh request
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

@csrf_protect
def main(request):
    context = {
        'page': 'strava-home'
    }

    if request.user.is_authenticated:
        try:
            # print(request.session.get('expiry'))
            # print(time.time())
            
            if 'access' in request.session:
                if time.time() >= request.session.get('expiry') - 3600:
                    print("REFRESHING TOKEN")
                    refresh_token(request)
                access_token = request.session.get('access')
                if request.method == "POST":
                    data = request.POST

                    if data.get('logout') == "1":
                        revoke_strava_token(request)
                        keys_to_clear = ['access', 'token_type', 'expiry', 'refresh', 'athlete']
                        for key in keys_to_clear:
                            if key in request.session:
                                del request.session[key]

                        return render(request, 'calc/strava/main.html', context)

                  

                try:
                    headers = {'Authorization': f'Bearer {access_token}'}
                    response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
                    
                    
                    if response.status_code == 200:
                        athlete_data = response.json()
                    elif response.status_code == 429:
                        raise RetryError(response=response)
                    else:
                        response.raise_for_status()
                    
                    userid = athlete_data['id']
                    response = requests.get(f'https://www.strava.com/api/v3/athletes/{userid}/stats', headers=headers)

                    if response.status_code == 200:
                        athlete_data = athlete_data | response.json()
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

                    elif response.status_code == 429:
                        raise RetryError(response=response)
                    else:
                        response.raise_for_status()

                    response = requests.get('https://www.strava.com/api/v3/athlete/activities', headers=headers)
                    
                    
                    if response.status_code == 200:
                        athlete_activities = response.json()
                        # datetime_obj.strftime("%d/%m/%y")
                        processed_athlete_activities = []
                        for athlete_activity in athlete_activities:
                            processed_athlete_activity = athlete_activity
                            processed_athlete_activity['distance'] = int(processed_athlete_activity['distance'] / 1000)
                            processed_athlete_activity['start_date_local'] = datetime.strptime(processed_athlete_activity['start_date_local'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
                            #processed_athlete_activity['start_date_local'].strftime("%d/%m/%y")
                            processed_athlete_activities.append(processed_athlete_activity)
                        # for key, value in athlete_activities[1].items():
                        #     print(f"{key}: {value}")


                    elif response.status_code == 429:
                        raise RetryError(response=response)
                    else:
                        response.raise_for_status()
                    
                
                except HTTPError as http_error:
                    # Handle other HTTP errors
                    context['error'] = f"HTTP error: {http_error}"
                    return render(request, 'calc/strava/main.html', context)
                # except RequestException as request_exception:
                #     # Handle other request-related exceptions
                #     context['error'] = f"Request exception: {request_exception}"
                #     return render(request, 'calc/strava/main.html', context)
                else:
                    context['athlete'], context['activities'] = converted_data, athlete_activities
                    

                return render(request, 'calc/strava/logged-in.html', context)
            elif 'code' in request.GET:
                # The authorization code returned by Strava
                authorization_code = request.GET['code']

                # Replace these values with your actual Strava application credentials
                client_id = CLIENT_ID
                client_secret = CLIENT_SECRET_KEY
                redirect_uri = 'http://127.0.0.1:8000/calc/strava'  # Should match the registered redirect URI

                # Strava token endpoint URL
                token_url = 'https://www.strava.com/oauth/token'

                # Request parameters for token exchange
                data = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': authorization_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                }

                # Make a POST request to the Strava token endpoint
                response = requests.post(token_url, data=data)

                if response.status_code == 200:
                    # Token exchange successful
                    access_token = response.json().get('access_token')


                    # Save the access token to the user's session
                    request.session['access'] = access_token
                    request.session['token_type'] = response.json().get('token_type')
                    request.session['expiry'] = response.json().get('expires_at')
                    request.session['refresh'] = response.json().get('refresh_token')
                    request.session['athlete'] = response.json().get('athlete')

                    # print("bearer: ", access_token, "\nType: ", request.session.get('token_type', None), 
                    #       "\nExpiry: ", request.session.get('expiry', None), "\nRefresh: ", request.session.get('refresh', None),
                    #       '\nAthlete: ', request.session.get('athlete', None))
                    # Your code to store or use the access token goes here

                    # Redirect the user to a success page or perform other actions
                    # return render(request, 'calc/strava/main.html', context)
                    return redirect('strava-home')
                else:
                    # Token exchange failed, handle the error
                    revoke_strava_token(request)
                    error_message = response.json().get('error_description', 'Token exchange failed')
                    context["error"] = error_message
                    print(response.json)
                    authorization_code = request.GET['code']
                    print("Authorization Code:", authorization_code)
                    response = requests.post(token_url, data=data)
                    print("Token Exchange Response:", response.json())

                    return render(request, 'calc/strava/main.html', context)
            else:
                return render(request, 'calc/strava/main.html', context)
        except RetryError as retry_error:
                    context['error'] = f"Rate limit exceeded: {retry_error}"
                    return render(request, 'calc/strava/main.html', context)
    else:
        return redirect('login')
    

@csrf_protect
def activity(request, activity_id):
    context = {'page': 'strava-home'}
    if request.user.is_authenticated:
        try:
            if 'access' in request.session:

                try:
                    #FOR TESTING
                    
                    if time.time() >= request.session.get('expiry') - 3600:
                        refresh_token(request)
                    access_token = request.session.get('access')
                    headers = {'Authorization': f'Bearer {access_token}'}
                    response = requests.get(f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=false", headers=headers)

                    if response.status_code == 200:
                        activity_data = response.json()
                        # for key, value in activity_data.items():
                            #     print(f"{key}: {value}\n")
                        # print(activity_data)
                    elif response.status_code == 429:
                        raise RetryError(response=response)
                    else:
                        response.raise_for_status()
                    #FOR TESTING
                    # activity_data = {}
                    # for key, value in TEMP_API_DATA.items():
                    #     activity_data[key] = value
                    #FOR TESTING

                except HTTPError as http_error:
                    context['error'] = f"HTTP error: {http_error}"
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
                    

                    # print(points)
                    context = context | {
                        'activity': activity_data,
                        'secret': {'mapbox': MAPBOX_SECRET_KEY, 'google': GOOGLEMAPS_SECRET_KEY},
                        'polyline': points,
                    }
                    return render(request, 'calc/strava/activity.html', context)
                
            else: return redirect('strava-home')
            
        except RetryError as retry_error:
                    context['error'] = f"Rate limit exceeded: {retry_error}"
                    return render(request, 'calc/strava/main.html', context)
    else: return redirect('login')