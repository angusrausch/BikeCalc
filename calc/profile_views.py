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
from .strava_views import revoke_strava_token


from .models import Tyre_Size, Cassettes, Chainrings, Blog, user_feedback, Bike
from django.contrib.auth.models import User


@csrf_protect
def login_view(request):
    if request.method == "POST":
        data = request.POST
        input_username = data.get("username").lower()
        input_password = data.get("password")

        user = authenticate(request, username=input_username, password=input_password)
        if user is not None:
            login(request, user)  # Pass the user object to the login function
            return redirect("profile")
        else:
            context = {
                'failed': True
            }
            return render(request, 'calc/authen/login.html', context)
    else:
        return render(request, 'calc/authen/login.html')
    
@csrf_protect
def sign_up(request):
    context = {}
    if request.method == "POST":
        data = request.POST
        input_username = data.get("username").lower()
        input_fname = data.get("fname")
        input_lname = data.get("lname")
        input_email = data.get("email")
        input_password = data.get("password")
        input_con_password = data.get("con_password")
        print(input_fname, input_lname)

        try:
            if input_username == "" or input_fname == "" or input_lname == "" or input_email == "" or input_password == "" or input_con_password == "":
                raise Exception("Please fill all fields")
            if User.objects.filter(username=input_username).exists():
                raise Exception("Username already in use")
            if User.objects.filter(email=input_email).exists():
                raise Exception("Email already in use")
            if input_password != input_con_password:
                raise Exception("Passwords do not match")
        except Exception as error:
            context = context | {"error": error}
        else:
            user = User.objects.create_user(input_username, input_email, input_password)
            user.last_name = input_lname
            user.first_name = input_fname
            user.save()
            return redirect("login")

    
    return render(request, 'calc/authen/sign_up.html', context)

def logout_view(request, prevpage="index"):
    # revoke_strava_token(request.session.get('access'))
    logout(request)
    keys_to_clear = ['access', 'token_type', 'expiry', 'refresh', 'athlete']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]    
    return redirect(prevpage)

@login_required(login_url="login")
def profile(request):
    user = request.user 

    bikes = Bike.objects.values("bike_name", "Chainring__chainring_name", "Cassette__cassette_name", "tyre__tyre_size_name").filter(user=request.user.id)
    # print(bikes)

    context = {'user': user,
               'page': 'profile',
               'bikes': bikes}
    if request.method == "POST":
        list_tyres = Tyre_Size.objects.all
        list_cassette = Cassettes.objects.all
        list_chainring = Chainrings.objects.all
        temp_context = {
            'tyre_size' : list_tyres,
            "cassettes" : list_cassette,
            "chainrings" : list_chainring,
            'new_bike': True
        }
        context = context | temp_context

        data = request.POST
        if data.get('type') == "1":
            temp_context = {
                'new_bike': True
            }
            context = context | temp_context

        elif data.get('type') == "2":
            
            try:
                #Name
                bike_name = data.get("bike_name")
                if bike_name == None or bike_name == "": raise Exception("No name selected")


                #Chainring
                chainring_input = data.get("chainring_selection")
                if chainring_input == "manual": 
                    manual_chainring = data.get("manual_chainring") 
                    if manual_chainring == None or manual_chainring == "":
                        raise Exception("No chainring selected")
                    else: 
                        selected_chainring = manual_chainring
                        chainring_size_nonint = selected_chainring.split(",")
                        chainring_size = []
                        for chainring in chainring_size_nonint:
                            chainring_size.append(int(chainring))
                        chainring_size.sort(reverse=True)
                        input_large = chainring_size[0]
                        input_middle = None
                        input_small = None
                        if len(chainring_size) == 2:
                            input_small = chainring_size[1]
                        elif len(chainring_size) == 3:
                            input_middle = chainring_size[1]
                            input_small = chainring_size[2]
                        selected_chainring_object = Chainrings.objects.filter(large=input_large, middle=input_middle, small=input_small).values("id")
                        if len(selected_chainring_object) == 0: #Nothing exists
                            chainring_name = f"User Chainring: {input_large}, {input_middle}, {input_small}"
                            chainring_instance = Chainrings(chainring_name=chainring_name, large=input_large, middle=input_middle, small=input_small, user_generated=True)
                            chainring_instance.save()
                            selected_chainring_object = Chainrings.objects.filter(large=input_large, middle=input_middle, small=input_small).values("id")


                        
                        chainring_selection = selected_chainring_object[0]['id']
                            
                        
                        
                else:
                    chainring_selection = chainring_input

                #Cassette
                cassette_input = data.get("cassette_selection")
                if cassette_input == "manual": 
                    manual_cassette = data.get("manual_cassette") 
                    if manual_cassette == None or manual_cassette == "":
                        raise Exception("No cassette selected")
                    else:

                        selected_cassette = manual_cassette

                        cassette_sprockets_nonint = selected_cassette.split(",")
                        cassette_sprockets = []
                        for sprocket in cassette_sprockets_nonint:
                            cassette_sprockets.append(int(sprocket))
                        cassette_sprockets.sort()
                        speeds = len(cassette_sprockets)
                        cassette = ""
                        for i in range(speeds):
                            cassette += str(cassette_sprockets[i])
                            if i < speeds - 1: cassette += ","
                        selected_cassette_object = Cassettes.objects.filter(sprockets=cassette).values("id")
                        if len(selected_cassette_object) == 0: #Nothing exists
                            cassette_name = f"User Cassette: {cassette_sprockets[0]}-{cassette_sprockets[len(cassette_sprockets) - 1]}"
                            cassette_instance = Cassettes(cassette_name=cassette_name, speeds=speeds, sprockets=cassette, user_generated=True)
                            cassette_instance.save()
                            selected_cassette_object = Cassettes.objects.filter(sprockets=cassette).values("id")



                        
                        cassette_selection = selected_cassette_object[0]['id']
                            
                        
                        
                else:
                    cassette_selection = cassette_input

                
                
                #Tyre
                tyre_input = data.get("tyre_selection")
                if tyre_input is None: raise Exception("No tyre selected")
            except Exception as error:
            #print(error)
                temp_context = {
                    "warning": error,
                    'new_bike': True
                }
                context = context | temp_context
                
            else: 
                chainring_instance = Chainrings.objects.get(id=chainring_selection)
                cassette_instance = Cassettes.objects.get(id=cassette_selection)
                tyre_instance = Tyre_Size.objects.get(id=tyre_input)

                # Create Bike instance and save
                bike_instance = Bike(bike_name=bike_name, Chainring=chainring_instance, Cassette=cassette_instance, tyre=tyre_instance, user=request.user)
                bike_instance.save()
        


    return render(request, 'calc/authen/main.html', context)


@login_required(login_url="login")
def table_view(request, table_name):
    if request.user.is_staff:
        if table_name:
        
            if table_name == "user_feedback":
                returned_table = user_feedback.objects.values('id', 'title', 'contact', 'body', 'date')
                columns = ['', 'Title', 'Body', 'Contact', 'date']
                table = []
                for row in returned_table:
                    table.append([row['id'], [row['title'], row['body'], row['contact'], row['date'].strftime("%d/%m/%y")]])
                
                context = {
                    'name': "Feedback",
                    'columns': columns,
                    'rows': table
                }
            
            elif table_name == "cassettes":
                returned_table = Cassettes.objects.values('id', 'cassette_name', 'speeds', 'sprockets')
                columns = ['', 'Name', 'Speed', 'Sprockets']
                table = []
                for row in returned_table:
                    table.append([row['id'], [row['cassette_name'], row['speeds'], row['sprockets']]])
                
                context = {
                    'name': "Cassettes",
                    'columns': columns,
                    'rows': table
                }

            elif table_name == "users":
                if request.user.is_superuser:
    
                    returned_table = User.objects.values('id', 'username', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'email')
                    columns = ['', 'Username', 'Name', 'Email', 'Type']
                    table = []
                    for row in returned_table:
                        if row['is_superuser'] is True: user_type = "Owner"
                        elif row['is_staff'] is True: user_type = "Staff"
                        else: user_type = "User"
                        name = row['first_name'] + " " + row['last_name']
                        table.append([row['id'], [row['username'], name, row['email'], user_type]])
                    
                    context = {
                        'name': "Users",
                        'columns': columns,
                        'rows': table
                    }
                else: return redirect('profile')
            elif table_name == "chainrings":
                returned_table = Chainrings.objects.values('id', 'chainring_name', 'large', 'middle', 'small')
                columns = ['', 'Name', 'Sizes']
                table = []
                for row in returned_table:

                    chainring_size = []
                    chainring_size.append(row["large"])
                    if row["middle"] != 0 and  row['middle'] is not None: chainring_size.append(row['middle'])
                    if row["small"] != 0 and row['small'] is not None: chainring_size.append(row['small'])
                    chainring_cogs = ""
                    for i in range(len(chainring_size)):
                        chainring_cogs += str(chainring_size[i])
                        if i  + 1 < len(chainring_size): chainring_cogs += ","

                    table.append([row['id'], [row['chainring_name'], chainring_cogs]])
                
                context = {
                    'name': "Chainring",
                    'columns': columns,
                    'rows': table
                }

            elif table_name == "tyres":
                returned_table = Tyre_Size.objects.values('id', 'tyre_size_name', 'tyre_circumference')
                columns = ['', 'Name', 'Circumference']
                table = []
                for row in returned_table:
                    table.append([row['id'], [row['tyre_size_name'], row['tyre_circumference']]])
                
                context = {
                    'name': "Tyres",
                    'columns': columns,
                    'rows': table
                }

            elif table_name == "bikes":
                returned_table = Bike.objects.values("id", "bike_name", "Chainring__chainring_name", "Cassette__cassette_name", "tyre__tyre_size_name", "user__first_name", 'user__last_name')
                columns = ['', 'Name', 'Chainring', 'Cassette', 'Tyre', 'User']
                table = []
                for row in returned_table:
                    table.append([row['id'], [row['bike_name'], row['Chainring__chainring_name'], row['Cassette__cassette_name'], row['tyre__tyre_size_name'], row['user__first_name'] + ' ' + row['user__last_name']]])
                
                context = {
                    'name': "Bikes",
                    'columns': columns,
                    'rows': table
                }

        context['page'] =  'profile'
        context['table_name'] = table_name
        return render(request, "calc/authen/table_view.html", context)
    else: return redirect('profile')

def edittable_view(request, table_name, id):
    if request.user.is_staff:
    
        context = {'page': 'index'}
        table_dict = {
            'user_feedback': user_feedback,
            'cassettes': Cassettes,
            'users': User,
            'chainrings': Chainrings,
            'tyres': Tyre_Size,
            'bikes': Bike,
        }
        table = table_dict.get(table_name)

        if not table:
            print(f"Table {table_name} not found")
            # You may want to handle this case appropriately, e.g., return a 404 response.

        try:
            # Use get() to retrieve a single record based on id
            table_data = table.objects.get(id=id)
            # Access all fields dynamically
            table_data_array = []
            for field_name, field_value in table_data.__dict__.items():
                if field_name == 'id':
                    continue

                # Determine the additional value based on the field type
                if isinstance(field_value, int):
                    additional_value = 0
                elif isinstance(field_value, str):
                    additional_value = 1
                elif isinstance(field_value, bool):
                    additional_value = 2
                else:
                    continue  

                table_data_array.append([field_name, field_value, additional_value])

            context['table_data'] = table_data_array
            context['name'] = table_name

            if request.method == 'POST':
                for field_name, _, additional_value in table_data_array:
                    if field_name != 'id':
                        new_value = request.POST.get(field_name, '')

                        # Handle empty string for non-boolean fields
                        if new_value == '':
                            continue

                        # Handle Boolean fields
                        if additional_value == 2:
                            new_value = bool(int(new_value))

                        setattr(table_data, field_name, new_value)

                # Update the record with the new values
                table_data.save()

        except table.DoesNotExist:
            print(f"{table_name} with id={id} not found")

        return render(request, 'calc/authen/table_editer.html', context)
    else: return redirect('profile')


def create_blog(request):
    if request.user.is_staff:
        
        current_datetime = datetime.now()
        current_date = current_datetime.strftime('%d-%m-%y')
        context = {
            "date" : current_date,
            "confirmation": "1",
            'page': 'create_blog'
            }
        if request.method == "POST":
            data = request.POST
            if data.get("submit") == "1":
                title_input = data.get("title_input")
                body_input = data.get("text_body")
                context_add = {
                    "title": title_input,
                    "body": body_input,
                }
                context = context | context_add
                context["confirmation"] = "2"
            elif data.get("submit") == "3":
                title_input = data.get("title_input")
                body_input = data.get("text_body")
                context_add = {
                    "title": title_input,
                    "body": body_input,
                }
                context = context | context_add
                context["confirmation"] = "1"
                #print(context)
            else: 
                title_input = data.get("title_input")
                body_input = data.get("text_body")
                db_date = current_datetime.strftime('%Y-%m-%d')
                blog_instance = Blog(title=title_input, body=body_input, date_field=db_date, user=request.user)
                blog_instance.save()

        posts = Blog.objects.values("title", "body", "date_field", "user__first_name").order_by('-date_field').filter(user = request.user.id)

        context_add = { "posts": posts }
        context = context | context_add

        # (request.user.first_name)

        return render(request, 'calc/authen/create_blog.html', context)
    else: return redirect('profile')


def create_bike(request):
    context = {
        'page': "index"
    }
    return render(request, 'calc/authen/create_bike.html', context)