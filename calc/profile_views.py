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
    logout(request)
    revoke_strava_token(request.session.get('access_token'))
    keys_to_clear = ['access', 'token_type', 'expiry', 'refresh', 'athlete']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]    
    return redirect(prevpage)

@login_required(login_url="login")
def profile(request):
    user = request.user 

    bikes = Bike.objects.values("bike_name", "Chainring__chainring_name", "Cassette__cassette_name", "tyre__tyre_size_name").filter(user=request.user.id)
    print(bikes)

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
                if chainring_input == None: raise Exception("No chainring selected")

                #Cassette
                cassette_input = data.get("cassette_selection")
                if cassette_input == None: raise Exception("No cassette selected")
                
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
                chainring_instance = Chainrings.objects.get(id=chainring_input)
                cassette_instance = Cassettes.objects.get(id=cassette_input)
                tyre_instance = Tyre_Size.objects.get(id=tyre_input)

                # Create Bike instance and save
                bike_instance = Bike(bike_name=bike_name, Chainring=chainring_instance, Cassette=cassette_instance, tyre=tyre_instance, user=request.user)
                bike_instance.save()
        


    return render(request, 'calc/authen/main.html', context)


@login_required(login_url="login")
def table_view(request, table_name):
    context = {'page': 'table_view'}
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
                'name': "Cassettes",
                'columns': columns,
                'rows': table
            }


        

        

    

    return render(request, "calc/authen/table_view.html", context)

def create_blog(request):
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

def create_bike(request):
    context = {
        'page': "index"
    }
    return render(request, 'calc/authen/create_bike.html', context)