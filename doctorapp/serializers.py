from .models import *
from userapp.models import *
from rest_framework import serializers
from rest_framework.fields import JSONField


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ['is_approved', 'status', 'created_at']
        
        def get_image(self, obj):
            if obj.image:
                return f"media/{obj.image}"
            return None

        def get_id_card(self, obj):
            if obj.id_card:
                return f"media/{obj.id_card}"
            return None
        
    def validate_email(self, value):
        # Email regex pattern
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        return value
    
    def validate_phone_number(self, value):
        # Note: Doctor model uses 'phone_number' field, not 'phone'
        import re
        phone_pattern = r'^[\+]?[1-9][0-9 \-\(\)\.]{7,}$'
        
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError("Please enter a valid phone number.")
        
        # Also check minimum length
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) < 10:
            raise serializers.ValidationError("Phone number must have at least 10 digits.")
        
        return value
        
        
class DoctorLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=Doctor
        fields=['email','password']
        
        
# class AppointmentSerializer(serializers.ModelSerializer):
#     pet_details = serializers.SerializerMethodField()

#     class Meta:
#         model = Appointment
#         fields = [
#             'id',
#             'pet_details',
#             'doctor',
#             'date',
#             'slot',
#             'reason',
#             'symptoms',
#         ]

#     def get_pet_details(self, obj):
#         return {
#             "id": obj.pet.id,
#             "name": obj.pet.name,
#             "category": obj.pet.category.petcategory if obj.pet.category else None,
#             "sub_category": obj.pet.sub_category.petsubcategory if obj.pet.sub_category else None,
#             "gender": obj.pet.gender,
#             "weight": obj.pet.weight,
#         }

class AppointmentSerializer(serializers.ModelSerializer):
    pet_details = serializers.SerializerMethodField()
    doctor_details = serializers.SerializerMethodField()
    slot_details = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_type',
            'pet_details',
            'doctor_details',
            'date',
            'slot',
            'slot_details',
            'reason',
            'symptoms',
            'status',
            'diagnosis_and_verdict',
            'notes'
        ]

    # 🐾 PET DETAILS
    def get_pet_details(self, obj):
        request = self.context.get('request')  # <-- IMPORTANT
        pet = obj.pet

        image_url = pet.pet_image.url if pet.pet_image else None
        if request and image_url:
            image_url = request.build_absolute_uri(image_url)

        return {
            "id": pet.id,
            "name": pet.name,
            "owner_name": pet.user.username if pet.user else None,
            "image": image_url,  # FULL URL instead of "media/..."
            "category": pet.category.petcategory if pet.category else None,
            "sub_category": pet.sub_category.petsubcategory if pet.sub_category else None,
            "gender": pet.gender,
            "weight": pet.weight,
            "health_condition": pet.health_condition,
        }

    # 👨‍⚕️ DOCTOR DETAILS
    def get_doctor_details(self, obj):
        return {
            "id": obj.doctor.id,
            "name": obj.doctor.full_name,
            "phone": obj.doctor.phone_number,
        }

    # 🕒 SLOT DETAILS
    def get_slot_details(self, obj):
        if not obj.slot:
            return None
        
        return {
            "slot_id": obj.slot.id,
            "time": f"{obj.slot.start_time.strftime('%H:%M')} - {obj.slot.end_time.strftime('%H:%M')}"
        }




class AppointmentUpdateSerializer(serializers.ModelSerializer):
    weight = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Appointment
        fields = ['diagnosis_and_verdict', 'notes', 'weight']
        
        
# class TreatmentHistorySerializer(serializers.ModelSerializer):
#     pet_name = serializers.CharField(source='pet.name', read_only=True)
#     weight = serializers.FloatField(source='pet.weight', read_only=True)
    

#     class Meta:
#         model = Appointment
#         fields = ['id', 'appointment_type','pet_name', 'weight', 'diagnosis_and_verdict', 'notes']
        

class TreatmentHistorySerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    pet_owner = serializers.CharField(source='pet.user.username', read_only=True)
    weight = serializers.FloatField(source='pet.weight', read_only=True)
    category = serializers.CharField(source='pet.category.petcategory', read_only=True)
    sub_category = serializers.CharField(source='pet.sub_category.petsubcategory', read_only=True)

    slot_start = serializers.SerializerMethodField()
    slot_end = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_type',
            'pet_name',
            'pet_owner',
            'weight',
            'category',
            'sub_category',
            'slot_start',
            'slot_end',
            'reason',
            'diagnosis_and_verdict',
            'notes'
        ]

    # Get slot start time
    def get_slot_start(self, obj):
        if obj.slot:
            return obj.slot.start_time.strftime("%H:%M")
        return None

    # Get slot end time
    def get_slot_end(self, obj):
        if obj.slot:
            return obj.slot.end_time.strftime("%H:%M")
        return None


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        
        
class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'  


class PrescriptionSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    appointment_date = serializers.DateField(source='appointment.date', read_only=True)
    appointment_type = serializers.CharField(source='appointment.appointment_type', read_only=True)
    diagnosis = serializers.CharField(source='appointment.diagnosis_and_verdict', read_only=True)
    medications = serializers.JSONField()
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'appointment',
            'doctor',
            'doctor_name',
            'pet',
            'pet_name',
            'diagnosis',
            'medications',
            'days_duration',
            'issued_date',
            'is_active',
            'notes',
            'appointment_date',
            'appointment_type'
        ]
        read_only_fields = ['id', 'issued_date', 'diagnosis']