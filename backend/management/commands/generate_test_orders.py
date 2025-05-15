from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.models import Company, Order, QuestionTemplate

class Command(BaseCommand):
    help = "Generate realistic test data for a restaurant-style company"

    def handle(self, *args, **kwargs):
        # Create the company
        company = Company.objects.create(
            name="The Hungry Hippo Café",
            phone_number="+1-555-321-9876",
            api_token="token_hungryhippo_001",
            instance_id="hippo_instance_101",
            webhook_token="webhook_hippo_secure"
        )
        self.stdout.write(self.style.SUCCESS(f"Created Company: {company.name}"))

        # Predefined orders and questions
        orders_data = [
            {
                "branch_name": "Downtown",
                "number": "ORD-1001",
                "customer_name": "Alice Johnson",
                "customer_phone_number": "923354949456",
                "details": "Order for delivery",
                "order_details": [
                    {"item": "Veggie Burger", "quantity": 2, "price": 8.99, "special_notes": "No onions"},
                    {"item": "Iced Latte", "quantity": 1, "price": 3.5, "special_notes": "Almond milk"},
                ],
            },
            {
                "branch_name": "Uptown",
                "number": "ORD-1002",
                "customer_name": "Brian Lee",
                "customer_phone_number": "923354949456",
                "details": "Pickup order",
                "order_details": [
                    {"item": "Pepperoni Pizza", "quantity": 1, "price": 12.0, "special_notes": "Extra cheese"},
                    {"item": "Root Beer", "quantity": 2, "price": 2.0, "special_notes": ""},
                ],
            },
            {
                "branch_name": "Midtown",
                "number": "ORD-1003",
                "customer_name": "Carlos Mendoza",
                "customer_phone_number": "923354949456",
                "details": "Dine-in reservation",
                "order_details": [
                    {"item": "Grilled Chicken Salad", "quantity": 1, "price": 10.5, "special_notes": "No dressing"},
                    {"item": "Sparkling Water", "quantity": 1, "price": 2.5, "special_notes": "Lemon slice"},
                ],
            },
            {
                "branch_name": "City Center",
                "number": "ORD-1004",
                "customer_name": "Diana Smith",
                "customer_phone_number": "923354949456",
                "details": "Order for delivery",
                "order_details": [
                    {"item": "Avocado Toast", "quantity": 2, "price": 7.0, "special_notes": "Add poached egg"},
                    {"item": "Flat White", "quantity": 2, "price": 3.75, "special_notes": ""},
                ],
            },
            {
                "branch_name": "Harbor View",
                "number": "ORD-1005",
                "customer_name": "Ethan Brown",
                "customer_phone_number": "923354949456",
                "details": "Walk-in takeout",
                "order_details": [
                    {"item": "Club Sandwich", "quantity": 1, "price": 9.5, "special_notes": "No mayo"},
                    {"item": "Lemonade", "quantity": 1, "price": 2.25, "special_notes": ""},
                ],
            },
        ]

        # Create orders and questions
        for order_data in orders_data:
            order = Order.objects.create(
                company=company,
                branch_name=order_data["branch_name"],
                number=order_data["number"],
                details=order_data["details"],
                order_at=timezone.now(),
                customer_name=order_data["customer_name"],
                customer_phone_number=order_data["customer_phone_number"],
                order_details=order_data["order_details"]
            )
            self.stdout.write(self.style.SUCCESS(f"Created Order: {order.number}"))

        self.stdout.write(self.style.SUCCESS("✅ Test data generation complete."))
