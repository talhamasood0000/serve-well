from django.contrib import admin
from .models import Company, Order


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number')
    search_fields = ('name', 'phone_number')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'company', 'time', 'customer_name', 'customer_phone_number')
    list_filter = ('company', 'time')
    search_fields = ('number', 'customer_name', 'customer_phone_number')
    ordering = ('-time',)
