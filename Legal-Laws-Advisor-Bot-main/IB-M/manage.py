# First, create a new Django project and app
# django-admin startproject legal_advisor
# cd legal_advisor
# python manage.py startapp bot

# bot/models.py
from django.db import models
from django.contrib.auth.models import User

class LegalInformation(models.Model):
    pattern = models.CharField(max_length=100)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pattern

class UserQuery(models.Model):
    user_name = models.CharField(max_length=100)
    query = models.CharField(max_length=100)
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user_name} - {self.query}"

# bot/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LegalInformation, UserQuery
from django.db.models import Q

def home(request):
    if 'user_name' in request.session:
        return redirect('query')
    return render(request, 'bot/home.html')

def start_session(request):
    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        if user_name:
            request.session['user_name'] = user_name
            return redirect('query')
    return redirect('home')

def query(request):
    if 'user_name' not in request.session:
        return redirect('home')
    
    user_name = request.session['user_name']
    user_queries = UserQuery.objects.filter(user_name=user_name)
    
    context = {
        'user_name': user_name,
        'user_queries': user_queries
    }
    return render(request, 'bot/query.html', context)

def get_legal_info(request):
    if request.method == 'POST' and 'user_name' in request.session:
        query_text = request.POST.get('query', '').lower()
        user_name = request.session['user_name']
        
        # Search for matching legal information
        legal_info = LegalInformation.objects.filter(
            Q(pattern__icontains=query_text)
        ).first()
        
        if legal_info:
            response = legal_info.response
        else:
            response = "Sorry, I couldn't find specific information about this query. Please try another search term or consult a legal professional."
        
        # Save the query and response
        UserQuery.objects.create(
            user_name=user_name,
            query=query_text,
            response=response
        )
        
        return render(request, 'bot/response.html', {
            'query': query_text,
            'response': response,
            'user_name': user_name
        })
    return redirect('query')

def logout(request):
    request.session.flush()
    return redirect('home')

# legal_advisor/urls.py
from django.contrib import admin
from django.urls import path
from bot import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('start-session/', views.start_session, name='start_session'),
    path('query/', views.query, name='query'),
    path('get-legal-info/', views.get_legal_info, name='get_legal_info'),
    path('logout/', views.logout, name='logout'),
]