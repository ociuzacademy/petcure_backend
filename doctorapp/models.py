from django.db import models
from datetime import datetime, time, timedelta


# Create your models here.
class Doctor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), 
        ('approved', 'Approved'),                     
        ('rejected', 'Rejected'),                     
    ]
    
    full_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=11, decimal_places=7,default=0.0)
    longitude=models.DecimalField(max_digits=11, decimal_places=7,default=0.0)
    image = models.ImageField(upload_to='doctors/profile/')
    id_card = models.ImageField(upload_to='doctors/id_cards/')
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=100, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
    def save(self, *args, **kwargs):
        # Detect approval change
        is_new = self.pk is None
        old_instance = None
        if not is_new:
            old_instance = Doctor.objects.filter(pk=self.pk).first()

        super().save(*args, **kwargs)

        # If newly approved, generate slots
        if not is_new and old_instance and not old_instance.is_approved and self.is_approved:
            self.status = 'approved'
            super().save(update_fields=['status'])
            self.generate_slots()

    def generate_slots(self):
        start_hour = 10
        end_hour = 17
        for hour in range(start_hour, end_hour):
            start_time = time(hour, 0)
            end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=1)).time()
            TimeSlot.objects.get_or_create(
                doctor=self,
                start_time=start_time,
                end_time=end_time
            )
    
    
class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='slots')
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} ({self.doctor.full_name})"
    
    