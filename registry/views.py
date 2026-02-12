from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Business

def business_list(request):
    businesses = Business.objects.all()
    return render(request, 'registry/business_list.html', {'businesses': businesses})

