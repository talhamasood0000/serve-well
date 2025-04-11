from django.db import models
from django.db.models import JSONField


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    api_token = models.CharField(max_length=100)
    instance_id = models.CharField(max_length=100)
    webhook_token = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="orders")
    number = models.CharField(max_length=100)
    details = models.TextField()    
    order_at = models.DateTimeField()
    customer_name = models.CharField(max_length=100)
    customer_phone_number = models.CharField(max_length=100)
    order_details = JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # [
    #     {
    #         "item": "name",
    #         "quantity": 2,
    #         "price": 100,
    #         "special_notes": "no salt"
    #     }

    # ]

    def __str__(self):
        return f"{self.number} - {self.company.name}"


class QuestionTemplate(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    question = models.CharField(max_length=100)
    priority = models.IntegerField()
    answer = models.TextField(null=True, blank=True)
    audio = models.FileField(upload_to='audio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.number} - {self.question}"

    @property
    def is_question_answered(self):
        return any([self.answer, self.audio])
    

class Analytics(TimeStampedModel):
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('pos_neutral', 'Positive + Neutral'),
        ('neg_neutral', 'Negative + Neutral'),
    ]

    EMOTION_CHOICES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('surprised', 'Surprised'),
        ('disgusted', 'Disgusted'),
        ('confused', 'Confused'),
        ('excited', 'Excited'),
        ('curious', 'Curious'),
        ('disappointed', 'Disappointed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sentiment_label = models.CharField(max_length=100, choices=SENTIMENT_CHOICES)
    sentiment_score = models.FloatField()
    emotions = models.CharField(max_length=100, choices=EMOTION_CHOICES)
    extracted_keywords = models.JSONField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.number} - {self.sentiment_label} - {self.emotions}"


class CompanyData(TimeStampedModel):
    
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    company_phone_number = models.CharField(max_length=100)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=100)
    order_details = models.JSONField(default=list)
    question_data = models.JSONField(default=list)
    analytics_data = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.order_number}"
