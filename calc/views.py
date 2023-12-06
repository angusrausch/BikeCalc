from django.http import HttpResponse
from django.template import loader
from django.http import Http404
from django.shortcuts import render, redirect
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from django.contrib.auth import login, authenticate
from django.urls import path
from django.views.decorators.csrf import csrf_protect

from .models import Tyre_Size, Cassettes, Chainrings, Blog, user_feedback, Bike
from django.contrib.auth.models import User

from django.http import JsonResponse
from mysecrets import MAPBOX_SECRET_KEY, GOOGLEMAPS_SECRET_KEY


def get_google_maps_key(request):
    return JsonResponse({'google_maps_key': GOOGLEMAPS_SECRET_KEY})
    


def index(request):
    context = {"page": "index"}
    return render(request, 'calc/index.html',context)
    #return HttpResponse("Hello, world. You're at the polls index.")


def about_me(request):
    posts = Blog.objects.values("title", "body", "date_field", "user__first_name").order_by('-date_field')
    context = {
        "page": "index",
        "posts": posts
    }
    return render(request, 'calc/about_me.html', context)

def ratio(request):
    list_cassette = Cassettes.objects.all
    list_chainring = Chainrings.objects.all
    list_bikes = Bike.objects.filter(user=request.user.id).all
    context = {
        "cassettes" : list_cassette,
        "chainrings_list" : list_chainring,
        "bikes" : list_bikes,
        "page": "ratio"
        }
    



    if request.method == "POST":
        
        try:

            data = request.POST
           
            bike_input = data.get("bike_selection")
            if bike_input != None:
                bike_data = Bike.objects.select_related('Chainring', 'Cassette', 'tyre', 'user').get(id=bike_input)
                
                #Chainring
                chainring_size = []
                chainring_size.append(bike_data.Chainring.large)
                if bike_data.Chainring.middle != 0 and  bike_data.Chainring.middle is not None: chainring_size.append(bike_data.Chainring.middle)
                if bike_data.Chainring.small != 0 and bike_data.Chainring.small is not None: chainring_size.append(bike_data.Chainring.small)
                chainring_cogs = ""
                for i in range(len(chainring_size)):
                    chainring_cogs += str(chainring_size[i])
                    if i  + 1 < len(chainring_size): chainring_cogs += ","
                #---

                #Cassette
                selected_cassette = bike_data.Cassette.sprockets
                cassette_name = bike_data.Cassette.cassette_name
                cassette_sprockets_nonint = selected_cassette.split(",")
                cassette_sprockets = []
                for sprocket in cassette_sprockets_nonint:
                    cassette_sprockets.append(int(sprocket))
                cassette_sprockets.sort(reverse=True)
                #---

            else:
                #Chainring
                chainring_input = data.get("chainring_selection")
                if chainring_input == "-- Manual Input --": 
                    selected_chainring = data.get("manual_chainring")
                    if selected_chainring == '': raise Exception("No chainring selected")
                    chainring_size_nonint = selected_chainring.split(",")
                    chainring_size = []
                    for chainring in chainring_size_nonint:
                        chainring_size.append(int(chainring))
                    chainring_name = ""

                else: 
                    selected_chainring_object = Chainrings.objects.filter(id=chainring_input).values("chainring_name", "large", "middle", "small")[0]
                    #print("Chainring: ", selected_chainring_object)
                    chainring_name = selected_chainring_object['chainring_name']
                    chainring_size = []
                    chainring_size.append(selected_chainring_object["large"])
                    if selected_chainring_object["middle"] != 0 and  selected_chainring_object['middle'] is not None: chainring_size.append(selected_chainring_object['middle'])
                    if selected_chainring_object["small"] != 0 and selected_chainring_object['small'] is not None: chainring_size.append(selected_chainring_object['small'])
                chainring_cogs = ""
                for i in range(len(chainring_size)):
                    chainring_cogs += str(chainring_size[i])
                    if i  + 1 < len(chainring_size): chainring_cogs += ","
                #---

                #Cassette
                cassette_input = data.get("cassette_selection")
                if cassette_input == "-- Manual Input --": 
                    selected_cassette = data.get("manual_cassette")
                    if selected_cassette == '': raise Exception("No cassette selected")
                    cassette_name = ""
                else: 
                    selected_cassette_object = Cassettes.objects.filter(id=cassette_input).values("cassette_name", "speeds", "sprockets")[0]
                    #print("Cassette: ",selected_cassette_object)
                    selected_cassette = selected_cassette_object['sprockets']
                    cassette_name = selected_cassette_object['cassette_name']
                cassette_sprockets_nonint = selected_cassette.split(",")
                cassette_sprockets = []
                for sprocket in cassette_sprockets_nonint:
                    cassette_sprockets.append(int(sprocket))
                cassette_sprockets.sort(reverse=True)
                #---
                





        except ValueError:
            #print("Please input only numbers spaced by ,")
            temp_context = {
                "warning": "Please input only numbers spaced by ,"
            }
            context = context | temp_context


        except Exception as error:
            #print(error)
            temp_context = {
                "warning": error
            }
            context = context | temp_context

        else:
            gear_ratios = []
            for chainring in chainring_size:
                temp_ratios = []
                for sprocket in cassette_sprockets:
                    temp_ratios.append(sprocket)
                gear_ratios.append([chainring, temp_ratios])


            ratios = []
            for ratio in gear_ratios:
                temp_ratios = []
                for sprocket in ratio[1]:
                    math_ratio = ratio[0]/sprocket
                    temp_ratios.append(round(math_ratio, 2))
                ratios.append([ratio[0], temp_ratios])
            
        
            
            temp_context = {
                "cassette_selection" : selected_cassette,
                "chainring_selection": chainring_cogs,
                "sprockets": cassette_sprockets,
                "chainrings": chainring_size,
                "ratios" : gear_ratios,
                "calculations": ratios
            }
            context = context | temp_context
    
    return render(request, 'calc/ratios.html', context)

def rollout(request):
    list_tyres = Tyre_Size.objects.all
    list_cassette = Cassettes.objects.all
    list_chainring = Chainrings.objects.all
    list_bikes = Bike.objects.filter(user=request.user.id).all

    context = {
        "page": "rollout",
        'tyre_size' : list_tyres,
        "cassettes" : list_cassette,
        "chainrings_list" : list_chainring,
        "bikes" : list_bikes,
        "rollout_selection" : 7
        }
    
    

    if request.method == "POST":
        
        try:

            data = request.POST
           
            
            bike_input = data.get("bike_selection")
            if bike_input != None:
                bike_data = Bike.objects.select_related('Chainring', 'Cassette', 'tyre', 'user').get(id=bike_input)
                
                #Chainring
                chainring_size = []
                chainring_size.append(bike_data.Chainring.large)
                if bike_data.Chainring.middle != 0 and  bike_data.Chainring.middle is not None: chainring_size.append(bike_data.Chainring.middle)
                if bike_data.Chainring.small != 0 and bike_data.Chainring.small is not None: chainring_size.append(bike_data.Chainring.small)
                chainring_cogs = ""
                for i in range(len(chainring_size)):
                    chainring_cogs += str(chainring_size[i])
                    if i  + 1 < len(chainring_size): chainring_cogs += ","
                #---

                #Cassette
                selected_cassette = bike_data.Cassette.sprockets
                cassette_name = bike_data.Cassette.cassette_name
                cassette_sprockets_nonint = selected_cassette.split(",")
                cassette_sprockets = []
                for sprocket in cassette_sprockets_nonint:
                    cassette_sprockets.append(int(sprocket))
                cassette_sprockets.sort(reverse=True)
                #---
            
                #Tyre
                tyre_input = bike_data.tyre.id
                tyre_name = bike_data.tyre.tyre_size_name
                tyre_circumference = bike_data.tyre.tyre_circumference
                #---

            else:
                #Chainring
                chainring_input = data.get("chainring_selection")
                if chainring_input == "-- Manual Input --": 
                    selected_chainring = data.get("manual_chainring")
                    if selected_chainring == '': raise Exception("No chainring selected")
                    chainring_size_nonint = selected_chainring.split(",")
                    chainring_size = []
                    for chainring in chainring_size_nonint:
                        chainring_size.append(int(chainring))
                    chainring_name = ""

                else: 
                    selected_chainring_object = Chainrings.objects.filter(id=chainring_input).values("chainring_name", "large", "middle", "small")[0]
                    #print("Chainring: ", selected_chainring_object)
                    chainring_name = selected_chainring_object['chainring_name']
                    chainring_size = []
                    chainring_size.append(selected_chainring_object["large"])
                    if selected_chainring_object["middle"] != 0 and  selected_chainring_object['middle'] is not None: chainring_size.append(selected_chainring_object['middle'])
                    if selected_chainring_object["small"] != 0 and selected_chainring_object['small'] is not None: chainring_size.append(selected_chainring_object['small'])
                chainring_cogs = ""
                for i in range(len(chainring_size)):
                    chainring_cogs += str(chainring_size[i])
                    if i  + 1 < len(chainring_size): chainring_cogs += ","
                #---

                #Cassette
                cassette_input = data.get("cassette_selection")
                if cassette_input == "-- Manual Input --": 
                    selected_cassette = data.get("manual_cassette")
                    if selected_cassette == '': raise Exception("No cassette selected")
                    cassette_name = ""
                else: 
                    selected_cassette_object = Cassettes.objects.filter(id=cassette_input).values("cassette_name", "speeds", "sprockets")[0]
                    #print("Cassette: ",selected_cassette_object)
                    selected_cassette = selected_cassette_object['sprockets']
                    cassette_name = selected_cassette_object['cassette_name']
                cassette_sprockets_nonint = selected_cassette.split(",")
                cassette_sprockets = []
                for sprocket in cassette_sprockets_nonint:
                    cassette_sprockets.append(int(sprocket))
                cassette_sprockets.sort(reverse=True)
                #---
                
                #Tyre
                tyre_input = data.get("tyre_selection")
                if tyre_input is None: raise Exception("No tyre selected")
                if tyre_input is not None:
                    selected_tyre_object = Tyre_Size.objects.filter(id=tyre_input).values("tyre_size_name", "tyre_circumference")[0]
                    #print("Tyre: ", selected_tyre_object)
                    tyre_name = selected_tyre_object['tyre_size_name']
                    tyre_circumference = selected_tyre_object['tyre_circumference']
                #---
            
            #rollout
            rollout_input = int(data.get("rollout_selection"))
            unit_selection = data.get("unit")
            if unit_selection == '1': multiplier = 0.001
            else: multiplier = 0.0393700787
            #---
        except ValueError:
            #print("Please input only numbers spaced by ,")
            temp_context = {
                "warning": "Please input only numbers spaced by ,"
            }
            context = context | temp_context
        except Exception as error:
            #print(error)
            temp_context = {
                "warning": error
            }
            context = context | temp_context
        else: 
                

            gear_ratios = []
            for chainring in chainring_size:
                temp_ratios = []
                for sprocket in cassette_sprockets:
                    temp_ratios.append(sprocket)
                gear_ratios.append([chainring, temp_ratios])


            rollout_values = []
            for ratio in gear_ratios:
                temp_ratios = []
                for sprocket in ratio[1]:
                    math_ratio = ratio[0]/sprocket
                    distance = math_ratio * tyre_circumference * multiplier
                    temp_ratios.append(round(distance, 2))
                rollout_values.append([ratio[0], temp_ratios])
            

            temp_context = {
                "rollout_selection" : rollout_input,
                "minimum_good_rollout" : rollout_input - 0.5,
                "cassette_selection" : selected_cassette,
                "chainring_selection": chainring_cogs,
                "tyre_selection": tyre_input,
                "sprockets": cassette_sprockets,
                "chainrings": chainring_size,
                "unit_selection": unit_selection,
                "ratios" : gear_ratios,
                "calculations": rollout_values
            }
            context = context | temp_context
    return render(request, 'calc/rollout.html', context)

def speed(request):
    user = request.user
    list_tyres = Tyre_Size.objects.all
    list_cassette = Cassettes.objects.all
    list_chainring = Chainrings.objects.all
    list_bikes = Bike.objects.filter(user=request.user.id).all
    context = {
        "page": "speed",
        'tyre_size' : list_tyres,
        "cassettes" : list_cassette,
        "chainrings" : list_chainring,
        "bikes" : list_bikes,
        "min_cadence": "70",
        "max_cadence": "110",
        "cadence_increment": "5",
        "slow_selection" : 20,
        "fast_selection" : 30
        }
    



    if request.method == "POST":
        


        try:

            data = request.POST
           
            bike_input = data.get("bike_selection")
            if bike_input != None:
                bike_data = Bike.objects.select_related('Chainring', 'Cassette', 'tyre', 'user').get(id=bike_input)
                
                #Chainring
                chainring_size = []
                chainring_size.append(bike_data.Chainring.large)
                if bike_data.Chainring.middle != 0 and  bike_data.Chainring.middle is not None: chainring_size.append(bike_data.Chainring.middle)
                if bike_data.Chainring.small != 0 and bike_data.Chainring.small is not None: chainring_size.append(bike_data.Chainring.small)
                chainring_cogs = ""
                for i in range(len(chainring_size)):
                    chainring_cogs += str(chainring_size[i])
                    if i  + 1 < len(chainring_size): chainring_cogs += ","
                #---

                #Cassette
                selected_cassette = bike_data.Cassette.sprockets
                cassette_name = bike_data.Cassette.cassette_name
                cassette_sprockets_nonint = selected_cassette.split(",")
                cassette_sprockets = []
                for sprocket in cassette_sprockets_nonint:
                    cassette_sprockets.append(int(sprocket))
                cassette_sprockets.sort(reverse=True)
                #---
            
                #Tyre
                tyre_input = bike_data.tyre.id
                tyre_name = bike_data.tyre.tyre_size_name
                tyre_circumference = bike_data.tyre.tyre_circumference
                #---

            else:
                #Chainring
                chainring_input = data.get("chainring_selection")
                if chainring_input == "-- Manual Input --": 
                    selected_chainring = data.get("manual_chainring")
                    if selected_chainring == '': raise Exception("No chainring selected")
                    chainring_size_nonint = selected_chainring.split(",")
                    chainring_size = []
                    for chainring in chainring_size_nonint:
                        chainring_size.append(int(chainring))
                    chainring_name = ""

                else: 
                    selected_chainring_object = Chainrings.objects.filter(id=chainring_input).values("chainring_name", "large", "middle", "small")[0]
                    #print("Chainring: ", selected_chainring_object)
                    chainring_name = selected_chainring_object['chainring_name']
                    chainring_size = []
                    chainring_size.append(selected_chainring_object["large"])
                    if selected_chainring_object["middle"] != 0 and  selected_chainring_object['middle'] is not None: chainring_size.append(selected_chainring_object['middle'])
                    if selected_chainring_object["small"] != 0 and selected_chainring_object['small'] is not None: chainring_size.append(selected_chainring_object['small'])
                chainring_cogs = ""
                for i in range(len(chainring_size)):
                    chainring_cogs += str(chainring_size[i])
                    if i  + 1 < len(chainring_size): chainring_cogs += ","
                #---

                #Cassette
                cassette_input = data.get("cassette_selection")
                if cassette_input == "-- Manual Input --": 
                    selected_cassette = data.get("manual_cassette")
                    if selected_cassette == '': raise Exception("No cassette selected")
                    cassette_name = ""
                else: 
                    selected_cassette_object = Cassettes.objects.filter(id=cassette_input).values("cassette_name", "speeds", "sprockets")[0]
                    #print("Cassette: ",selected_cassette_object)
                    selected_cassette = selected_cassette_object['sprockets']
                    cassette_name = selected_cassette_object['cassette_name']
                cassette_sprockets_nonint = selected_cassette.split(",")
                cassette_sprockets = []
                for sprocket in cassette_sprockets_nonint:
                    cassette_sprockets.append(int(sprocket))
                cassette_sprockets.sort(reverse=True)
                #---
                
                #Tyre
                tyre_input = data.get("tyre_selection")
                if tyre_input is None: raise Exception("No tyre selected")
                if tyre_input is not None:
                    selected_tyre_object = Tyre_Size.objects.filter(id=tyre_input).values("tyre_size_name", "tyre_circumference")[0]
                    #print("Tyre: ", selected_tyre_object)
                    tyre_name = selected_tyre_object['tyre_size_name']
                    tyre_circumference = selected_tyre_object['tyre_circumference']
                #---

            #Cadence
            min_cadence = int(data.get("min_cadence"))
            max_cadence = int(data.get("max_cadence"))
            cadence_inc = int(data.get("increment"))
            if min_cadence == '' or max_cadence == '' or cadence_inc == '': raise Exception("Error in cadence")
            if min_cadence > max_cadence: raise Exception("Miniumum cadence must be less than maximum cadence \nMinimum: ", min_cadence, " Maximum: ", max_cadence)
            if cadence_inc <= 0: raise Exception("Cadence increment must be positive number more than 0")
            #---

            #Units
            unit_selection = int(data.get("units"))
            if unit_selection == 1: 
                unit = "Kph"
                speed_modifer = 16670
            else: 
                unit = "Mph"
                speed_modifer = 26820
            #---

            #Speed
            slow_speed = int(data.get("slow_selection"))
            fast_speed = int(data.get("fast_selection"))
            #---





        except ValueError:
            #print("Please input only numbers spaced by ,")
            temp_context = {
                "warning": "Please input only numbers spaced by ,"
            }
            context = context | temp_context

        # except Exception as error:
        #     #print(error)
        #     temp_context = {
        #         "warning": error
        #     }
        #     context = context | temp_context
        else:
            gear_ratios = []
            for chainring in chainring_size:
                for sprocket in cassette_sprockets:
                    gear_ratios.append([chainring, sprocket])
            
            current_cadence = min_cadence
            cadence_sets = []
            while current_cadence <= max_cadence:
                cadence_sets.append(current_cadence)
                current_cadence += cadence_inc

            speeds = []
            for ratio in gear_ratios:
                temp_speeds = []
                for cadence in cadence_sets:
                    math_ratio = ratio[0] / ratio[1]
                    mm_per_minute = math_ratio * cadence * tyre_circumference
                    final_speed = mm_per_minute/speed_modifer
                    temp_speeds.append(round(final_speed,2))
                

                speeds.append({"ratio": ratio, "speed": temp_speeds})
            
            temp_context = {
                'calculations' : speeds ,
                "cadence_sets" : cadence_sets,
                "units_selection": unit_selection,
                "units" : unit,
                "cassette_selection" : selected_cassette,
                "chainring_selection": chainring_cogs,
                "tyre_selection": tyre_input,
                "min_cadence": min_cadence,
                "max_cadence": max_cadence,
                "cadence_increment": cadence_inc,    
                "slow_selection" : slow_speed,
                "fast_selection" : fast_speed

            }
            context = context | temp_context

    return render(request, 'calc/speed.html', context)

    '''
    lass Wheel_size(models.Model):
    Wheel_size_name = models.CharField(max_length=100)
    def __str__(self):
        return self.Wheel_size_name
        '''
    
def feedback(request):

    if request.method == "POST":
        data = request.POST
        user_contact = data.get("contact")
        feedback_title = data.get("title")
        feedback_body = data.get("text_body")
        current_datetime = datetime.now()
        current_date = current_datetime.strftime('%Y-%m-%d')
        #print("TITLE: ", user_feedback, "\nBody: ", feedback_body, "Contact: ",user_contact)

        feedback_instance = user_feedback(
            title=feedback_title,  # Use the correct field names
            contact=user_contact,
            body=feedback_body,
            date=current_date
        )
        feedback_instance.save()
        context = {
            "page": "feedback",
            "is_post": True
        }
    else:
        context = {
            "page": "feedback",
            "is_post": False
        }
        
    
    return render(request, 'calc/feedbackform.html', context)