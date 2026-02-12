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
        # Create 15-minute slots (4 slots per hour)
        # Morning session: 10:00 AM to 12:00 PM
        for hour in range(10, 12):
            for minute in [0, 15, 30, 45]:  # 4 slots per hour at 15-minute intervals
                start_time = time(hour, minute)
                end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=15)).time()
                TimeSlot.objects.get_or_create(
                    doctor=self,
                    start_time=start_time,
                    end_time=end_time
                )
        
        # Skip lunch break (12:00 PM to 1:00 PM)
        # No slots created for this interval
        
        # Afternoon session: 1:00 PM to 5:00 PM
        for hour in range(13, 17):
            for minute in [0, 15, 30, 45]:  # 4 slots per hour at 15-minute intervals
                start_time = time(hour, minute)
                end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=15)).time()
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


class CancelledSlot(models.Model):
    """
    Tracks slots cancelled by doctor for specific dates
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='cancelled_slots')
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='cancelled_dates')
    date = models.DateField()
    cancelled_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('doctor', 'slot', 'date')  # Prevent duplicate cancellation records
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.slot} cancelled on {self.date}"
    
class DoctorFeedback(models.Model):
    RATING_CHOICES = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='feedbacks')
    user_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=RATING_CHOICES)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for {self.doctor.full_name} by {self.user_name} - {self.get_rating_display()}"
    
class DoctorComplaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='complaints')
    user_name = models.CharField(max_length=100)
    complaint = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Complaint against {self.doctor.full_name} by {self.user_name} - {self.status}"
    

class Prescription(models.Model):
    """Prescription table for completed appointments"""
    appointment = models.ForeignKey('userapp.Appointment', on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    pet = models.ForeignKey('userapp.Pet', on_delete=models.CASCADE, related_name='prescriptions')
    
    
    # Prescription details - multiple medications supported
    medications = models.JSONField(default=list, help_text="List of medications, each with name, dosage, food_timing, time_of_day")
    
    days_duration = models.PositiveIntegerField(help_text="For how many days", default=7)
    
    # Prescription metadata
    issued_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Prescription #{self.id} for {self.pet.name} - Dr. {self.doctor.full_name}"