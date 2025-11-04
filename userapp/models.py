from django.db import models
from adminapp.models import *
from doctorapp.models import *
from deliveryapp.models import *

# Create your models here.
class User(models.Model):
    username=models.CharField(max_length=100)
    email=models.CharField(max_length=100)
    address= models.CharField(max_length=100,default="")
    password=models.CharField(max_length=100)
    phone=models.CharField(max_length=20,default="")
    image=models.ImageField(upload_to="user_image", null=True, blank=True)
    latitude = models.DecimalField(max_digits=11, decimal_places=7,default=0.0)
    longitude=models.DecimalField(max_digits=11, decimal_places=7,default=0.0)
    number_of_pets = models.IntegerField(default=0)
    
    
class Pet(models.Model):
    GENDER_CHOICES = (('male', 'Male'), ('female', 'Female'))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    category = models.ForeignKey(PetCategory, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(PetSubcategory, on_delete=models.CASCADE)
    weight = models.FloatField()
    pet_image = models.ImageField(upload_to='pets/')
    health_condition = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class ProductBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('order placed', 'Order placed'),
        ('order on the way', 'Order on the way'),
        ('order delivered', 'Order delivered'),
        ('order cancelled', 'Order cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estimated_delivery_date = models.DateTimeField(null=True, blank=True)
    assigned_agent = models.ForeignKey(DeliveryAgent,on_delete=models.SET_NULL,null=True,blank=True,related_name="assigned_order",
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
    
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('upi', 'UPI'),
        ('card', 'Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    expiry_date = models.CharField(max_length=5, blank=True, null=True)
    cvv_number = models.CharField(max_length=4, blank=True, null=True)
    payment_status = models.CharField(max_length=50, default='success')
    payment_date = models.DateTimeField(auto_now_add=True)
    
from django.db import models
from doctorapp.models import Doctor, TimeSlot
from userapp.models import Pet  # assuming Pet model exists
from datetime import date
class Appointment(models.Model):
    REASON_CHOICES = [
        ('Vaccine', 'Vaccine'),
        ('Routine checkup', 'Routine checkup'),
        ('Sickness', 'Sickness'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    symptoms = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'slot', 'date')  # prevent duplicate booking

    def __str__(self):
        return f"{self.pet.name} - {self.doctor.name} ({self.date} {self.slot})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-unlock slot after the appointment date passes
        if self.date < date.today():
            self.slot.is_available = True
            self.slot.save(update_fields=['is_available'])