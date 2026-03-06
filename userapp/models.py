from django.db import models
from adminapp.models import *
from doctorapp.models import *
from deliveryapp.models import *
from django.core.exceptions import ValidationError
from datetime import datetime

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
class User(models.Model):
    username=models.CharField(max_length=100)
    email=models.CharField(max_length=100)
    address= models.CharField(max_length=100,default="")
    place = models.CharField(max_length=50, choices=PLACE_CHOICES, default='thrissur', help_text="Place in Thrissur district")
    password=models.CharField(max_length=100)
    phone=models.CharField(max_length=20,default="")
    image=models.ImageField(upload_to="user_image", null=True, blank=True)
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
    pet_image = models.ImageField(upload_to='pets/', null=True, blank=True)
    health_condition = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_age(self):
        from datetime import date
        if self.birth_date:
            today = date.today()
            
            # Handle future dates (test data issue)
            if self.birth_date > today:
                return "Future date"
            
            # Calculate age in days
            age_days = (today - self.birth_date).days
            
            if age_days < 28:  # Less than 4 weeks
                return f"{age_days // 7} weeks"
            elif age_days < 365:  # Less than 1 year
                months = age_days // 30
                return f"{months} months"
            else:
                years = age_days // 365
                remaining_days = age_days % 365
                months = remaining_days // 30
                
                if months > 0:
                    return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months > 1 else ''}"
                else:
                    return f"{years} year{'s' if years > 1 else ''}"
        return "Unknown"
    
    
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
    assigned_agent = models.ForeignKey(DeliveryAgent,on_delete=models.SET_NULL,null=True,blank=True,related_name="assigned_order")

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
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True) #payment.order is not null → Payment is for a product order
    appointment = models.ForeignKey('Appointment', on_delete=models.CASCADE, null=True, blank=True) #payment.appointment is not null → Payment is for a doctor appointment
    # A payment can be for EITHER order OR appointment (not both)
    
    PAYMENT_FOR_CHOICES = [
        ('order', 'Product Order'),
        ('appointment', 'Doctor Appointment'),
    ]
    payment_for = models.CharField(max_length=20, choices=PAYMENT_FOR_CHOICES)
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
    
    APPOINTMENT_TYPES = [
        ('clinical', 'Clinical'),
        ('audio_call', 'Audio Call'),
    ]
    
    REASON_CHOICES = [
        ('Vaccine', 'Vaccine'),
        ('Routine checkup', 'Routine checkup'),
        ('Sickness', 'Sickness'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES,blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    diagnosis_and_verdict = models.TextField(blank=True, null=True)
    # verdict = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    vaccine = models.ForeignKey('adminapp.Vaccine', on_delete=models.SET_NULL, null=True, blank=True) #This vaccine field in the Appointment model is a ForeignKey to the Vaccine model from adminapp where the vaccine ID is stored when booking a vaccine appointment.
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('payment_completed', 'Payment Completed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    
    # class Meta:
    #     unique_together = ('doctor', 'slot', 'date')  # prevent duplicate booking

    def __str__(self):
        return f"{self.pet.name} - {self.doctor.full_name} ({self.date} {self.slot})"
    
    def save(self, *args, **kwargs):
        # Check if this is an update (not a new appointment)
        if self.pk:
            print(f"DEBUG: In save() method, self.pk = {self.pk}")
            print(f"DEBUG: self.status = {self.status}")
            
            old_appointment = Appointment.objects.get(pk=self.pk)
            print(f"DEBUG: old_appointment.status = {old_appointment.status}")
            
            # Check if status is being changed to 'cancelled'
            if old_appointment.status != 'cancelled' and self.status == 'cancelled':
                print("DEBUG: Status changing to cancelled, checking time...")
                
                # Skip time check if doctor is cancelling (indicated by notes containing "Doctor cancelled")
                if not self.notes or "Doctor cancelled" not in self.notes:
                    # Calculate time difference between now and appointment
                    from django.utils import timezone
                    import pytz
                    
                    # Get local timezone (Asia/Kolkata for India)
                    local_tz = pytz.timezone('Asia/Kolkata')
                    now_local = timezone.now().astimezone(local_tz)
                    
                    # Create appointment datetime in local timezone
                    appointment_datetime_local = local_tz.localize(datetime.combine(self.date, self.slot.start_time))
                    
                    time_difference = appointment_datetime_local - now_local
                    
                    # Check if cancelling less than 3 hours before appointment
                    if time_difference.total_seconds() < 10800:  # 3 hours in seconds
                        raise ValidationError("Appointments can only be cancelled at least 3 hours before the scheduled time.")
        
        super().save(*args, **kwargs)
        
        # Skip slot availability update if doctor is cancelling
        if not self.notes or "Doctor cancelled" not in self.notes:
            # Count non-cancelled appointments for this slot
            booked_count = Appointment.objects.filter(
                doctor=self.doctor,
                slot=self.slot,
                date=self.date
            ).exclude(status='cancelled').count()
            
            # Update slot availability based on count (4 max per 15-minute slot)
            if booked_count >= 4:
                self.slot.is_available = False
            else:
                self.slot.is_available = True
                
            self.slot.save(update_fields=['is_available'])
            

from django.core.validators import MaxValueValidator, MinValueValidator

class Feedback(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback #{self.id}"
    
    
class Complaint(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Complaint #{self.id}"