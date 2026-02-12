from django.contrib import admin
from .models import *

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'city', 'status')
    search_fields = ('name', 'registration_number')
    list_filter = ('status', 'city')
