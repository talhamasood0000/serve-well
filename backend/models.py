from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    number = models.CharField(max_length=100)
    details = models.TextField()    
    time = models.DateTimeField()
    customer_name = models.CharField(max_length=100)
    customer_phone_number = models.CharField(max_length=100)


    def __str__(self):
        return f"{self.number} - {self.company.name}"
