from django.db import models

# District choices for Kerala
DISTRICT_CHOICES = [
    ('thrissur', 'Thrissur'),
    ('tvm', 'Thiruvananthapuram'),
    ('kollam', 'Kollam'),
    ('pathanamthitta', 'Pathanamthitta'),
    ('alappuzha', 'Alappuzha'),
    ('kottayam', 'Kottayam'),
    ('idukki', 'Idukki'),
    ('ernakulam', 'Ernakulam'),
    ('palakkad', 'Palakkad'),
    ('malappuram', 'Malappuram'),
    ('kozhikode', 'Kozhikode'),
    ('wayanad', 'Wayanad'),
    ('kannur', 'Kannur'),
    ('kasargod', 'Kasaragod'),
]

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
    place = models.CharField(max_length=50, choices=DISTRICT_CHOICES, default='thrissur', help_text="District as place")
    profile_image = models.ImageField(upload_to='deliveryboys/profile/', null=True, blank=True)
    id_card_image = models.ImageField(upload_to='deliveryboys/id_cards/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # New field
    status = models.CharField(max_length=100, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Agent's current location latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Agent's current location longitude")
    service_radius = models.IntegerField(default=10, help_text="Service radius in kilometers")
    is_available = models.BooleanField(default=True, help_text="Whether agent is currently available for deliveries")

