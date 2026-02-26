from django.db import models

# Place choices for Thrissur district only
PLACE_CHOICES = [
    ('thrissur', 'Thrissur'),
    ('kunnamkulam', 'Kunnamkulam'),
    ('chalakkudy', 'Chalakkudy'),
    ('kodungallur', 'Kodungallur'),
    ('guruvayur', 'Guruvayur'),
    ('iriyur', 'Iriyur'),
    ('cholapuram', 'Cholapuram'),
    ('elavally', 'Elavally'),
    ('karumathra', 'Karumathra'),
    ('kattakampal', 'Kattakampal'),
    ('manalur', 'Manalur'),
    ('minalur', 'Minalur'),
    ('mullassery', 'Mullassery'),
    ('nadathara', 'Nadathara'),
    ('naduvil', 'Naduvil'),
    ('nellayi', 'Nellayi'),
    ('ollur', 'Ollur'),
    ('panamkutty', 'Panamkutty'),
    ('pandipulam', 'Pandipulam'),
    ('parappukkara', 'Parappukkara'),
    ('peedika', 'Peedika'),
    ('perakam', 'Perakam'),
    ('perumannur', 'Perumannur'),
    ('pullazhi', 'Pullazhi'),
    ('puthenchira', 'Puthenchira'),
    ('thangalur', 'Thangalur'),
    ('thayyur', 'Thayyur'),
    ('thiruvilwamala', 'Thiruvilwamala'),
    ('thozhiyur', 'Thozhiyur'),
    ('velur', 'Velur'),
    ('venmanad', 'Venmanad'),
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
    place = models.CharField(max_length=50, choices=PLACE_CHOICES, default='thrissur', help_text="Place in Thrissur district")
    profile_image = models.ImageField(upload_to='deliveryboys/profile/', null=True, blank=True)
    id_card_image = models.ImageField(upload_to='deliveryboys/id_cards/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # New field
    status = models.CharField(max_length=100, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    service_radius = models.IntegerField(default=10, help_text="Service radius in kilometers")
    is_available = models.BooleanField(default=True, help_text="Whether agent is currently available for deliveries")

