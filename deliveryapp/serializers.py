from .models import *
from rest_framework import serializers
from adminapp.models import *
from userapp.models import *

class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAgent
        fields = ['id', 'username', 'email', 'phone', 'address', 'place', 'profile_image', 'id_card_image', 'status', 'is_approved', 'created_at', 'latitude', 'longitude', 'service_radius', 'is_available']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Add place display name
        if instance.place:
            from .models import DISTRICT_CHOICES
            place_dict = dict(DISTRICT_CHOICES)
            rep['place_display'] = place_dict.get(instance.place, instance.place)
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
        

class DeliveryBoyLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=DeliveryAgent 
        fields=['email','password']
        

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product_name', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    phone_number = serializers.CharField(source='user.phone', read_only=True)
    address = serializers.CharField(source='user.address', read_only=True)
    latitude = serializers.DecimalField(source='user.latitude',max_digits=11, decimal_places=7, read_only=True)
    longitude = serializers.DecimalField(source='user.longitude',max_digits=11, decimal_places=7, read_only=True)
    agent_name = serializers.CharField(source='assigned_agent.full_name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_name','phone_number','latitude','address','longitude','agent_name', 'order_date',
            'status', 'total_amount', 'estimated_delivery_date',
            'items'
        ]
