from .models import *
from rest_framework import serializers
from adminapp.models import *
from doctorapp.models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields='__all__'
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.image:
            rep['image'] = instance.image.url
        return rep
        
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
    images = ProductImageSerializer(many=True, read_only=True)  # nested images

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock',
            'productcategory', 'petcategory', 'petsubcategory',
            'created_at', 'images'
        ]
        

class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'product_name', 'quantity', 'total_price']
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

class AppointmentSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    slot = serializers.PrimaryKeyRelatedField(queryset=TimeSlot.objects.all())

    class Meta:
        model = Appointment
        fields = ['id', 'pet', 'doctor', 'date', 'slot', 'reason', 'symptoms']

    def validate(self, data):
        doctor = data.get('doctor')
        slot = data.get('slot')
        appointment_date = data.get('date')

        # ✅ 1. Future or today check
        if appointment_date < date.today():
            raise serializers.ValidationError("You can only book appointments for today or future dates.")

        # ✅ 2. Ensure slot belongs to this doctor
        if slot.doctor != doctor:
            raise serializers.ValidationError("Selected slot does not belong to this doctor.")

        # ✅ 3. Prevent double booking on same date
        if Appointment.objects.filter(doctor=doctor, slot=slot, date=appointment_date).exists():
            raise serializers.ValidationError("This slot is already booked for the selected date.")

        return data

    def create(self, validated_data):
        # ✅ Simply create — no need to mark slot unavailable globally
        appointment = Appointment.objects.create(**validated_data)
        return appointment

class PetsSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.petcategory', read_only=True)
    sub_category_name = serializers.CharField(source='sub_category.petsubcategory', read_only=True)

    class Meta:
        model = Pet
        fields = '__all__'  # keeps your existing fields
        read_only_fields = ['id', 'created_at', 'user']