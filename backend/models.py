from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    api_token = models.CharField(max_length=100)
    instance_id = models.CharField(max_length=100)
    webhook_token = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="orders")
    number = models.CharField(max_length=100)
    details = models.TextField()    
    time = models.DateTimeField()
    customer_name = models.CharField(max_length=100)
    customer_phone_number = models.CharField(max_length=100)


    def __str__(self):
        return f"{self.number} - {self.company.name}"


class QuestionTemplate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    question = models.CharField(max_length=100)
    priority = models.IntegerField()
    answer = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.order.number} - {self.question}"

    @property
    def is_question_answered(self):
        return self.answer is None