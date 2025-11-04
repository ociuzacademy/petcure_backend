from django.db import models

# Create your models here.
class DeliveryAgent(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), 
        ('approved', 'Approved'),                     
        ('rejected', 'Rejected'),                     
    ]
    
    username = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='deliveryboys/profile/', null=True, blank=True)
    id_card_image = models.ImageField(upload_to='deliveryboys/id_cards/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # New field
    status = models.CharField(max_length=100, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

