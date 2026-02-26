from decimal import Decimal
from .models import *
from rest_framework import serializers
from adminapp.models import *
from doctorapp.models import *
from datetime import datetime
from adminapp.models import Vaccine

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields='__all__'
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.image:
            rep['image'] = instance.image.url
        # Convert place code to display name
        if instance.place:
            from .models import PLACE_CHOICES
            place_dict = dict(PLACE_CHOICES)
            rep['place_display'] = place_dict.get(instance.place, instance.place)
        return rep
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.image:
            rep['image'] = instance.image.url
        return rep
    
    def validate_email(self, value):
        # Email regex pattern
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        return value
    
    def validate_phone(self, value):
        # Phone regex pattern: 10 digits, can start with +, optional spaces/dashes
        import re
        phone_pattern = r'^[\+]?[1-9][0-9 \-\(\)\.]{7,}$'
        
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError("Please enter a valid phone number.")
        
        # Also check minimum length
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) < 10:
            raise serializers.ValidationError("Phone number must have at least 10 digits.")
        
        return value
    
        
class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['email','password']
        
class ViewPetcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=PetCategory
        fields='__all__'
        
# class PetSubcategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PetSubcategory
#         fields = ['petcategory_id','id', 'petsubcategory']

class PetSubcategorySerializer(serializers.ModelSerializer):
    petsubcategory_id = serializers.IntegerField(source='id', read_only=True)
    category_id = serializers.IntegerField(source='petcategory.id', read_only=True)

    class Meta:
        model = PetSubcategory
        fields = ['petsubcategory_id', 'category_id', 'petsubcategory']
        
class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user']
        
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    productcategory_name = serializers.CharField(source='productcategory.productcategory', read_only=True)
    petcategory_name = serializers.CharField(source='petcategory.petcategory', read_only=True)
    petsubcategory_name = serializers.CharField(source='petsubcategory.petsubcategory', read_only=True)


    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock',
            'productcategory', 'productcategory_name',
            'petcategory', 'petcategory_name',
            'petsubcategory', 'petsubcategory_name',
            'created_at', 'images'
        ]
class ProductImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']    

class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_images = ProductImagesSerializer(source='product.images', many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 
            'user', 
            'product', 
            'product_name', 
            'product_images',
            'quantity', 
            'total_price'
        ]
        read_only_fields = ['id', 'total_price', 'product_name']
        

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        
        
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'product_price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'order_date',
            'status',
            'total_amount',
            'estimated_delivery_date',
            'items'
        ]



from rest_framework import serializers
from .models import Appointment
from doctorapp.models import Doctor, TimeSlot
from datetime import date

# class AppointmentSerializer(serializers.ModelSerializer):
#     doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
#     doctor_phone = serializers.CharField(source='doctor.phone_number', read_only=True)
#     slot_time = serializers.CharField(source='slot.time', read_only=True)
#     pet_name = serializers.CharField(source='pet.name', read_only=True)

#     class Meta:
#         model = Appointment
#         fields = [
#             'id',
#             'pet',          # pet id
#             'pet_name',
#             'doctor',       # doctor id
#             'doctor_name',
#             'doctor_phone',
#             'date',
#             'slot',         # slot id
#             'slot_time',
#             'reason',
#             'symptoms',
#             'diagnosis',
#             'verdict',
#             'notes'
#         ]

#     def validate(self, data):
#         doctor = data.get('doctor')
#         slot = data.get('slot')
#         appointment_date = data.get('date')

#         # ✅ 1. Future or today check
#         if appointment_date < date.today():
#             raise serializers.ValidationError("You can only book appointments for today or future dates.")

#         # ✅ 2. Ensure slot belongs to this doctor
#         if slot.doctor != doctor:
#             raise serializers.ValidationError("Selected slot does not belong to this doctor.")

#         # ✅ 3. Prevent double booking on same date
#         if Appointment.objects.filter(doctor=doctor, slot=slot, date=appointment_date).exists():
#             raise serializers.ValidationError("This slot is already booked for the selected date.")

#         return data

#     def create(self, validated_data):
#         # ✅ Simply create — no need to mark slot unavailable globally
#         appointment = Appointment.objects.create(**validated_data)
#         return appointment


# class AppointmentSerializer(serializers.ModelSerializer):
#     doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
#     doctor_phone = serializers.CharField(source='doctor.phone_number', read_only=True)
#     slot_time = serializers.CharField(source='slot.time', read_only=True)
#     pet_name = serializers.CharField(source='pet.name', read_only=True)

#     class Meta:
#         model = Appointment
#         fields = [
#             'id',
#             'appointment_type',
#             'pet',
#             'pet_name',
#             'doctor',
#             'doctor_name',
#             'doctor_phone',
#             'date',
#             'slot',
#             'slot_time',
#             'reason',
#             'symptoms',
#             'diagnosis_and_verdict',
#             'notes'
#         ]

#     def validate(self, data):
#         appointment_type = data.get('appointment_type')
#         doctor = data.get('doctor')
#         slot = data.get('slot')
#         appointment_date = data.get('date')

#         # Date check
#         if appointment_date < date.today():
#             raise serializers.ValidationError("Date must be today or future.")

#         # Slot must belong to doctor
#         if slot.doctor != doctor:
#             raise serializers.ValidationError("Selected slot does not belong to this doctor.")

#         # Prevent booking same slot
#         if Appointment.objects.filter(doctor=doctor, slot=slot, date=appointment_date).exists():
#             raise serializers.ValidationError("This slot is already booked for this date.")

#         # Clinical → reason is required
#         if appointment_type == "clinical" and not data.get("reason"):
#             raise serializers.ValidationError("Reason is required for clinical appointments.")

#         # Audio call → symptoms required
#         if appointment_type == "audio_call" and not data.get("symptoms"):
#             raise serializers.ValidationError("Symptoms are required for audio call.")

#         return data
#     def create(self, validated_data):
#         # ✅ Simply create — no need to mark slot unavailable globally
#         appointment = Appointment.objects.create(**validated_data)
#         return appointment


class AppointmentSerializer(serializers.ModelSerializer): #Used for creating/validating new appointments
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_phone = serializers.CharField(source='doctor.phone_number', read_only=True)
    slot_time = serializers.CharField(source='slot.time', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    vaccine_name = serializers.CharField(source='vaccine.vaccine_name', read_only=True)
    vaccine_age = serializers.CharField(source='vaccine.recommended_age', read_only=True)
    disease_protected = serializers.CharField(source='vaccine.disease_protected', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_type',
            'pet',
            'pet_name',
            'doctor',
            'doctor_name',
            'doctor_phone',
            'date',
            'slot',
            'slot_time',
            'reason',
            'vaccine',
            'symptoms',
            'status',
            'diagnosis_and_verdict',
            'notes',
            'vaccine_name',
            'vaccine_age', 
            'disease_protected',
            'fee_amount'
        ]

    def validate(self, data):
        appointment_type = data.get('appointment_type')
        doctor = data.get('doctor')
        slot = data.get('slot')
        appointment_date = data.get('date')

        # Date check
        if appointment_date < date.today():
            raise serializers.ValidationError("Date must be today or future.")

        # Slot must belong to doctor
        if slot.doctor != doctor:
            raise serializers.ValidationError("Selected slot does not belong to this doctor.")

        # Check if slot has been cancelled by doctor
        if not slot.is_available:
            raise serializers.ValidationError("This slot has been cancelled by the doctor and is not available for booking.")
        
        # 👉 Allow max 4 appointments for the same doctor-slot-date (15-minute slots)
        existing = Appointment.objects.filter(
            doctor=doctor,
            slot=slot,
            date=appointment_date
        ).exclude(status='cancelled').count()

        if existing >= 4:
            raise serializers.ValidationError("This slot is fully booked (maximum 4 appointments).")
        
        # Clinical → reason required
        if appointment_type == "clinical" and not data.get("reason"):
            raise serializers.ValidationError("Reason is required for clinical appointments.")

        # Audio call → symptoms required
        if appointment_type == "audio_call" and not data.get("symptoms"):
            raise serializers.ValidationError("Symptoms are required for audio call.")

        # Check if trying to cancel appointment
        if self.instance and data.get('status') == 'cancelled':
            from django.utils import timezone
            appointment_datetime = timezone.make_aware(
                datetime.combine(self.instance.date, self.instance.slot.start_time)
            )
            time_difference = appointment_datetime - timezone.now()
            
            # 3 hours = 10800 seconds
            if time_difference.total_seconds() < 10800:
                raise serializers.ValidationError(
                    "Appointments can only be cancelled at least 3 hours before the scheduled time."
                )
            
        # Vaccine appointment → vaccine required
        if data.get("reason") == "Vaccine" and not data.get("vaccine"):
            raise serializers.ValidationError("Vaccine selection is required for vaccine appointments.")
                # Set default fee for vaccine appointments
        
        if data.get("reason") == "Vaccine" and not data.get("fee_amount"):
            data["fee_amount"] = Decimal("100.00")
            
        return data

class AppointmentsSerializer(serializers.ModelSerializer): #Used for reading/displaying appointments
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_phone = serializers.CharField(source='doctor.phone_number', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    # add explicit fields for slot start/end and slot id
    slot_id = serializers.SerializerMethodField(read_only=True)
    slot_start = serializers.SerializerMethodField(read_only=True)
    slot_end = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_type',
            'pet',
            'pet_name',
            'doctor',
            'doctor_name',
            'doctor_phone',
            'date',
            'slot',
            'slot_id',
            'slot_start',
            'slot_end',
            'reason',
            'vaccine',
            'symptoms',
            'status',
            'diagnosis_and_verdict',
            'notes',
            'fee_amount'
        ]

    def get_slot_id(self, obj):
        return obj.slot.id if obj.slot else None

    def get_slot_start(self, obj):
        if not obj.slot or not getattr(obj.slot, 'start_time', None):
            return None
        # Format as HH:MM (24h) or change to '%I:%M %p' for 12h
        return obj.slot.start_time.strftime('%H:%M')

    def get_slot_end(self, obj):
        if not obj.slot or not getattr(obj.slot, 'end_time', None):
            return None
        return obj.slot.end_time.strftime('%H:%M')
    
class PetsSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.petcategory', read_only=True)
    sub_category_name = serializers.CharField(source='sub_category.petsubcategory', read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = '__all__'  # keeps your existing fields
        read_only_fields = ['id', 'created_at', 'user']

    def get_age(self, obj):
        if obj.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - obj.birth_date.year
            if today.month < obj.birth_date.month or (today.month == obj.birth_date.month and today.day < obj.birth_date.day):
                age -= 1
            
            if age == 0:
                # Calculate in months for young pets
                months = today.month - obj.birth_date.month
                if today.day < obj.birth_date.day:
                    months -= 1
                if months <= 0:
                    weeks = (today - obj.birth_date).days // 7
                    return f"{weeks} weeks" if weeks < 4 else f"{months} months"
                return f"{months} months"
            return f"{age} years"
        return "Unknown"



class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        
        
class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'
    
class VaccineSerializer(serializers.ModelSerializer):
    subcategory_name = serializers.CharField(source='subcategory.petsubcategory', read_only=True)
    subcategory_id = serializers.IntegerField(source='subcategory.id', read_only=True)
    
    class Meta:
        model = Vaccine
        fields = ['id', 'subcategory_id', 'subcategory_name', 'vaccine_name', 'recommended_age', 'disease_protected', 'booster_required', 'booster_timing', 'annual_revaccination']
