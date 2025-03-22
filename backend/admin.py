from django.contrib import admin
from backend.models import Company, Order, QuestionTemplate


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


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ('order', 'question', 'priority', 'is_question_answered')
    search_fields = ('name', 'content')
