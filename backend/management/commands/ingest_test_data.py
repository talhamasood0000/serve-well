import csv
import json
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from backend.models import Company, Order, QuestionTemplate, Analytics, CompanyData

class Command(BaseCommand):
    help = 'Clears all data and ingests test companies and orders from CSV files'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        
        # Delete all data from all models
        CompanyData.objects.all().delete()
        Analytics.objects.all().delete()
        QuestionTemplate.objects.all().delete()
        Order.objects.all().delete()
        Company.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('All existing data cleared!'))
        
        # Paths to test data files
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        company_file = os.path.join(base_dir, 'test_data', 'test_company.csv')
        orders_file = os.path.join(base_dir, 'test_data', 'test_orders.csv')
        
        # Create test companies from CSV
        self.stdout.write('Creating test companies from CSV...')
        companies = {}
        
        try:
            with open(company_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    company = Company.objects.create(
                        name=row.get('name', ''),
                        phone_number=row.get('phone_number', ''),
                        api_token=row.get('api_token', ''),
                        instance_id=row.get('instance_id', ''),
                        webhook_token=row.get('webhook_token', '')
                    )
                    companies[row.get('id', str(company.id))] = company
                    self.stdout.write(f'Created company: {company.name}')
            
            self.stdout.write(self.style.SUCCESS('Test companies created successfully!'))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f'Company file not found: {company_file}'))
            return 
        
        # Create test orders from CSV
        self.stdout.write('Creating test orders from CSV...')
        try:
            with open(orders_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    company_id = row.get('company_id', 1)
                    company = companies.get(company_id)
                    
                    if not company:
                        continue
                    

                    order_details = []
                    if row.get('order_details'):
                        try:
                            order_details = json.loads(row.get('order_details'))
                        except json.JSONDecodeError:
                            continue
                    
                    # Create order
                    order = Order.objects.create(
                        company=company,
                        branch_name=row.get('branch_name', ''),
                        details=row.get('details', ''),
                        order_at=timezone.now() if not row.get('order_at') else timezone.make_aware(
                            datetime.strptime(row.get('order_at'), '%Y-%m-%d %H:%M:%S')
                        ),
                        customer_name=row.get('customer_name', ''),
                        customer_phone_number=row.get('customer_phone_number', ''),
                        order_details=order_details
                    )
                    
                    # Create default question templates for each order
                    questions = [
                        {"question": "How was your overall experience?", "priority": 1},
                        {"question": "Rate the quality from 1-5!", "priority": 2},
                    ]
                    
                    for q in questions:
                        QuestionTemplate.objects.create(
                            order=order,
                            question=q["question"],
                            priority=q["priority"],
                        )
                    
                    self.stdout.write(f'Created order: {order.number}')
            
            self.stdout.write(self.style.SUCCESS('Test orders created successfully!'))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f'Orders file not found: {orders_file}'))
            return
        
        self.stdout.write(self.style.SUCCESS('Test data ingestion complete!'))

