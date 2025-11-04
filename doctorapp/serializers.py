from .models import *
from userapp.models import *
from rest_framework import serializers


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
        
class DoctorLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=Doctor
        fields=['email','password']
        
        
class AppointmentSerializer(serializers.ModelSerializer):
    pet_details = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'pet_details',
            'doctor',
            'date',
            'slot',
            'reason',
            'symptoms',
        ]

    def get_pet_details(self, obj):
        return {
            "id": obj.pet.id,
            "name": obj.pet.name,
            "category": obj.pet.category.petcategory if obj.pet.category else None,
            "sub_category": obj.pet.sub_category.petsubcategory if obj.pet.sub_category else None,
            "gender": obj.pet.gender,
            "weight": obj.pet.weight,
        }
