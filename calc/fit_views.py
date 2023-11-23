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
from fitparse.base import FitFile, FitHeaderError

import math
import threading
import queue
import concurrent.futures
from datetime import datetime, timezone
import os
from .models import Tyre_Size, Cassettes, Chainrings, Blog, user_feedback, Bike
from .fitter import processing
from django.contrib.auth.models import User


@csrf_protect
def fitviewer(request):
    context = {
        'page': 'fit-home'
    }

    if request.method == "POST" and request.FILES.get("file_upload"):
        uploaded_file = request.FILES["file_upload"]
        data = request.POST
        try:
            crank = float(data.get('crank_length'))
            fit_file = FitFile(uploaded_file)
            processed_file = processing(fit_file, crank)
        except FitHeaderError as e:
            context = context | {'warning': "Not valid Fit file"}
        except Exception as e:
            print(f"Error processing file: {e}")
        else:
            context = context | {'data': processed_file, 
                                    'filename': uploaded_file.name,
                                    'crank_length': crank,
                                    }

    return render(request, 'calc/fit/home.html', context)
