from .models import *
from rest_framework import serializers
from adminapp.models import *
from userapp.models import *

class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAgent 
        fields = ['username','email','phone','password','address','city','profile_image','id_card_image']

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
    agent_name = serializers.CharField(source='assigned_agent.full_name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_name', 'agent_name', 'order_date',
            'status', 'total_amount', 'estimated_delivery_date',
            'items'
        ]
