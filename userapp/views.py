from django.shortcuts import get_object_or_404, render,redirect
from .models import *
from adminapp.models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status,viewsets,generics
from rest_framework.views import APIView
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from math import radians, sin, cos, sqrt, atan2


# Create your views here.
class UserRegistrationView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post']
    
    def create(self, request, *args, **kwargs):
        serializer =self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            response_data = {
                "status":"success",
                "message" : "User Created Successfully",
                "data" : serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data = {
                "status":"failed",
                "message": "Invalid Details",
                "errors": serializer.errors,
                "data": request.data
            }
            return Response(response_data,status=status.HTTP_400_BAD_REQUEST)
        

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            email = request.data.get("email")
            password = request.data.get("password")
            
            try:
                user = User.objects.get(email=email)
                if password == user.password:
                    response_data = {
                        "status": "success",
                        "message": "User logged in successfully",
                        "user_id": str(user.id),
                        "data": request.data
                    }
                    request.session['id'] = user.id
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "status": "failed",
                        "message": "Invalid credentials",
                        "data": request.data
                    }, status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                return Response({
                    "status": "failed",
                    "message": "User not found",
                    "data": request.data
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response({
            "status": "failed",
            "message": "Invalid input",
            "errors": serializer.errors,
            "data": request.data
        }, status=status.HTTP_400_BAD_REQUEST)

        

class UserProfileView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class=UserSerializer
    
    def list(self, request, *args,**kwargs):
        user_id= request.query_params.get('user_id')
        
        if user_id:
            try:
                user= self.queryset.get(id=user_id)
                serializer = self.get_serializer(user)
                return Response(serializer.data,status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"detail":"User not found"},status=status.HTTP_404_NOT_FOUND)
        else:
            return super().list(request,*args,**kwargs)
        
class UpdateUserProfileView(generics.UpdateAPIView):
    queryset=User.objects.all()
    serializer_class=UserSerializer
    http_method_names=["patch"]
    
    def update(self,request,*args,**kwargs):
        user_id=request.data.get('user_id')
        if not user_id:
            return Response({"detail":"User not found"},status=status.HTTP_404_NOT_FOUND)
        
        try:
            user=User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail":"User not found"},status=status.HTTP_404_NOT_FOUND)
        
        
        serializer=self.get_serializer(user,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({"detail":"Profile updated successfully.","data":serializer.data},status=status.HTTP_200_OK)

class ViewPetCategoryView(viewsets.ReadOnlyModelViewSet):
    queryset = PetCategory.objects.all()
    serializer_class = ViewPetcategorySerializer

    def  list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class ViewPetSubCategoryView(viewsets.ReadOnlyModelViewSet):
    serializer_class = PetSubcategorySerializer

    # You must define get_queryset
    def get_queryset(self):
        category_id = self.request.query_params.get('category_id')
        if not category_id:
            return PetSubcategory.objects.none()  # empty queryset if no category_id
        return PetSubcategory.objects.filter(petcategory_id=category_id)

    # Optional: override list() to return custom response
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({
                "success": False,
                "message": "No subcategories found for this category."
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "subcategories": serializer.data
        }, status=status.HTTP_200_OK)


class AddPetAPIView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        user = get_object_or_404(User, id=user_id)

        serializer = PetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)  # assign pet to the user

            # Increment the user's number_of_pets
            user.number_of_pets += 1
            user.save()

            return Response({
                "success": True,
                "message": "Pet added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
class UserPetsListAPIView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({
                "success": False,
                "message": "user_id parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)
        pets = Pet.objects.filter(user=user)
        serializer = PetsSerializer(pets, many=True)

        return Response({
            "success": True,
            "user_id": user.id,
            "number_of_pets": user.number_of_pets,
            "pets": serializer.data
        }, status=status.HTTP_200_OK)
        
class PetDetailAPIView(APIView):
    def get(self, request):
        pet_id = request.query_params.get('pet_id')
        if not pet_id:
            return Response({
                "success": False,
                "message": "pet_id parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetsSerializer(pet)
        return Response({
            "success": True,
            "pet": serializer.data
        }, status=status.HTTP_200_OK)
        

class UpdatePetDetailsView(APIView):
    def patch(self, request):
        pet_id = request.data.get('pet_id')  # ✅ read from body instead of query params
        if not pet_id:
            return Response({'error': 'pet_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PetSerializer(pet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Pet details updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ViewAllProductsView(APIView):
    def get(self, request):
        products = Product.objects.all().order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        petcategory_id = request.query_params.get('pet_category_id')
        
        if petcategory_id:
            products = Product.objects.filter(petcategory_id=petcategory_id)
        else:
            products = Product.objects.all()

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    

class ProductDetailsView(APIView):
    def get(self, request):
        product_id = request.query_params.get('product_id')  # get the 'id' from query params
        if not product_id:
            return Response({"error": "Product ID is required as a query parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AddToCartView(APIView):
    def post(self, request):
        serializer = CartSerializer(data=request.data)

        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')

        # Validate presence of IDs
        if not user_id or not product_id:
            return Response({'error': 'user and product are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if already exists in cart
        cart_item, created = Cart.objects.get_or_create(
            user_id=user_id,
            product=product,
            defaults={'quantity': 1, 'total_price': product.price}
        )

        # If exists, update
        if not created:
            cart_item.quantity += 1
            cart_item.total_price = cart_item.quantity * product.price
            cart_item.save()

        # Serialize and return
        serializer = CartSerializer(cart_item)
        return Response({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_item': serializer.data
        }, status=status.HTTP_200_OK)


class CartItemListView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')

        # Validate
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch cart items
        cart_items = Cart.objects.filter(user_id=user_id)

        if not cart_items.exists():
            return Response({'message': 'No items in the cart'}, status=status.HTTP_200_OK)

        # Serialize data
        serializer = CartSerializer(cart_items, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'cart_items': serializer.data
        }, status=status.HTTP_200_OK)
        
class UpdateCartQuantityByIdView(APIView):
    def patch(self, request):
        cart_id = request.data.get('cart_id')
        quantity = request.data.get('quantity')

        # Validate input
        if not cart_id or quantity is None:
            return Response({'error': 'cart_id and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
        except ValueError:
            return Response({'error': 'Quantity must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity < 1:
            return Response({'error': 'Quantity must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update quantity and total price
        cart_item.quantity = quantity
        cart_item.total_price = cart_item.product.price * quantity
        cart_item.save()

        serializer = CartSerializer(cart_item)
        return Response({
            'success': True,
            'message': 'Cart quantity updated successfully',
            'cart_item': serializer.data
        }, status=status.HTTP_200_OK)
        

# class MakePurchaseView(APIView):
#     def post(self, request):
#         user_id = request.data.get('user_id')

#         if not user_id:
#             return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

#         # Get all cart items for the user
#         cart_items = Cart.objects.filter(user_id=user_id)
#         if not cart_items.exists():
#             return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

#         # Calculate total amount
#         total_amount = sum(item.total_price for item in cart_items)

#         # Order date is now
#         order_date = timezone.now()

#         # Estimated delivery = 5 days from order date
#         estimated_delivery_date = order_date + timedelta(days=5)

#         # Create Order (status defaults to 'pending')
#         order = Order.objects.create(
#             user_id=user_id,
#             total_amount=total_amount,
#             order_date=order_date,
#             estimated_delivery_date=estimated_delivery_date
#         )

#         # Add cart items to order
#         order.cart_items.set(cart_items)
#         order.save()

#         # Optionally, clear the cart
#         cart_items.delete()

#         return Response({
#             'success': True,
#             'message': 'Order created successfully',
#             'order_id': order.id,
#             'amount_to_pay': float(total_amount),
#             'estimated_delivery_date': estimated_delivery_date.strftime("%Y-%m-%d %H:%M:%S")
#         }, status=status.HTTP_201_CREATED)

class MakePurchaseView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')

        # Validate user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all cart items for this user
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total amount
        total_amount = sum(item.total_price for item in cart_items)

        # Create new order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            status='pending',
            estimated_delivery_date=timezone.now() + timedelta(days=5)
        )

        # Move cart items to OrderItem
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,
                total_price=item.total_price
            )

        # Clear cart after successful order
        cart_items.delete()

        # Success response
        return Response({
            'success': True,
            'message': 'Order placed successfully!',
            'order_id': order.id,
            'amount_to_pay': str(total_amount),
            'estimated_delivery_date': order.estimated_delivery_date.strftime('%Y-%m-%d'),
        }, status=status.HTTP_201_CREATED)
        

class BuyNowView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')

        if not user_id or not product_id:
            return Response({'error': 'user_id and product_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if product already in user's cart
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': 1, 'total_price': product.price}
        )

        # If exists, increment quantity
        if not created:
            cart_item.quantity += 1
            cart_item.total_price = cart_item.quantity * product.price
            cart_item.save()

        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=cart_item.total_price,
            status='pending',
            estimated_delivery_date=timezone.now() + timedelta(days=5)
        )

        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=cart_item.quantity,
            product_price=product.price,
            total_price=cart_item.total_price
        )

        # Remove item from cart after purchase
        cart_item.delete()

        return Response({
            'success': True,
            'message': 'Product purchased successfully!',
            'order_id': order.id,
            'amount_to_pay': str(order.total_amount),
            'estimated_delivery_date': order.estimated_delivery_date.strftime('%Y-%m-%d')
        }, status=status.HTTP_201_CREATED)


class RemoveCartView(generics.DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def destroy(self, request, *args, **kwargs):
        cart_item_id = request.query_params.get('cart_id')

        if not cart_item_id:
            return Response(
                {"status": "failed", "message": "cart_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = Cart.objects.get(id=cart_item_id)
            cart_item.delete()
            return Response(
                {"status": "success", "message": "Product removed from cart successfully"},
                status=status.HTTP_200_OK
            )
        except Cart.DoesNotExist:
            return Response(
                {"status": "failed", "message": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "failed", "message": "An error occurred", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearCartView(generics.DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')

        if not user_id:
            return Response(
                {"status": "failed", "message": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_items = Cart.objects.filter(user_id=user_id)
        if not cart_items.exists():
            return Response(
                {"status": "success", "message": "Cart is already empty"},
                status=status.HTTP_200_OK
            )

        cart_items.delete()
        return Response(
            {"status": "success", "message": "All items removed from cart successfully"},
            status=status.HTTP_200_OK
        )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils import timezone

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_order_confirmation_email(order, payment):
    """
    Sends order confirmation email to the user after successful payment.
    """
    subject = f"Order #{order.id} Placed Successfully"
    
    # HTML content
    html_message = render_to_string('order_confirmation.html', {
        'user': order.user,
        'order': order,
        'payment': payment,
    })
    # Plain text fallback
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],  # ✅ Send only to the user
        html_message=html_message,
        fail_silently=False,
    )


def reduce_stock_after_payment(order):
    """Reduce product stock after successful payment"""
    for item in OrderItem.objects.filter(order=order):
        product = item.product
        if product.stock >= item.quantity:
            product.stock -= item.quantity
        else:
            product.stock = 0
        product.save()


class UPIPaymentView(APIView):
    """Handles UPI Payment"""

    def post(self, request):
        data = request.data
        data["payment_method"] = "upi"

        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()

            order = get_object_or_404(Order, id=payment.order.id, user_id=payment.user.id)

            # Validate amount
            if payment.amount != order.total_amount:
                payment.payment_status = 'failed'
                payment.save()
                return Response({"error": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Payment successful
            payment.payment_status = "success"
            payment.save()

            # ✅ Update order
            order.status = "order placed"
            order.estimated_delivery_date = timezone.now() + timedelta(days=5)
            order.save()

            # ✅ Reduce stock
            reduce_stock_after_payment(order)

            # ✅ Send email only to that user's email
            send_order_confirmation_email(order, payment)

            return Response({
                "message": "UPI payment successful and order placed",
                "order_id": order.id,
                "amount": str(payment.amount)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardPaymentView(APIView):
    """Handles Card Payment"""

    def post(self, request):
        data = request.data
        data["payment_method"] = "card"

        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()

            order = get_object_or_404(Order, id=payment.order.id, user_id=payment.user.id)

            # Validate amount
            if payment.amount != order.total_amount:
                payment.payment_status = 'failed'
                payment.save()
                return Response({"error": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Payment successful
            payment.payment_status = "success"
            payment.save()

            # ✅ Update order
            order.status = "order placed"
            order.estimated_delivery_date = timezone.now() + timedelta(days=5)
            order.save()

            # ✅ Reduce stock
            reduce_stock_after_payment(order)

            # ✅ Send email only to that user
            send_order_confirmation_email(order, payment)

            return Response({
                "message": "Card payment successful and order placed",
                "order_id": order.id,
                "amount": str(payment.amount)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.core.mail import EmailMultiAlternatives

class CancelOrderView(APIView):
    """Allows user to cancel an order without authentication"""

    authentication_classes = []  # 👈 Disable authentication
    permission_classes = []      # 👈 Disable permission checks

    def patch(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {"status": "error", "message": "Order ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get order
        order = get_object_or_404(Order, id=order_id)

        # Prevent cancelling delivered orders
        if order.status in ["order delivered", "order cancelled"]:
            return Response(
                {"status": "error", "message": "This order cannot be cancelled now."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        order.status = "order cancelled"
        order.save()

        # Send email to user
        subject = f"❌ Your Order #{order.id} Has Been Cancelled"
        context = {"user": order.user, "order": order}
        html_content = render_to_string("order_cancelled.html", context)
        text_content = f"Hi {order.user.username}, your order #{order.id} has been cancelled successfully."

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        return Response(
            {"status": "success", "message": "Order cancelled and email sent."},
            status=status.HTTP_200_OK
        )
        
        
class OrderListView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        orders = Order.objects.filter(user_id=user_id).order_by('-order_date')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class OrderDetailView(APIView):
    def get(self, request):
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NearbyDoctorsView(APIView):
    def get(self, request):
        try:
            user_lat = float(request.query_params.get('latitude'))
            user_lon = float(request.query_params.get('longitude'))
        except (TypeError, ValueError):
            return Response({"error": "Latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)

        radius_km = 10  # within 10 KM radius
        nearby_doctors = []

        for doctor in Doctor.objects.filter(is_approved=True):
            distance = self.calculate_distance(
                user_lat, user_lon,
                float(doctor.latitude), float(doctor.longitude)
            )

            if distance <= radius_km:
                nearby_doctors.append({
                    "id": doctor.id,
                    "full_name": doctor.full_name,
                    "email": doctor.email,
                    "phone_number": doctor.phone_number,
                    "address": doctor.address,
                    "latitude": float(doctor.latitude),
                    "longitude": float(doctor.longitude),
                    # ✅ media-relative path
                    "image": f"media/{doctor.image.name}" if doctor.image else None,
                    "id_card": f"media/{doctor.id_card.name}" if doctor.id_card else None,
                    "distance_km": round(distance, 2),
                })

        # Sort doctors by distance
        nearby_doctors = sorted(nearby_doctors, key=lambda x: x["distance_km"])

        return Response({"doctors": nearby_doctors}, status=status.HTTP_200_OK)

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Haversine formula to calculate distance between two coordinates (in KM)."""
        R = 6371  # Radius of Earth in KM
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
    
class DoctorSlotListView(APIView):
    """
    GET /doctor/slots/?doctor_id=<id>&date=YYYY-MM-DD
    Returns all slots for the doctor with availability for that date.
    """

    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        requested_date = request.query_params.get('date')

        # ✅ 1. Validate parameters
        if not doctor_id:
            return Response({"error": "doctor_id parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not requested_date:
            return Response({"error": "date parameter is required (YYYY-MM-DD)."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ 2. Parse date
        try:
            appointment_date = datetime.strptime(requested_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ 3. Ensure future or today’s date
        if appointment_date < date.today():
            return Response({"error": "Cannot view slots for past dates."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ 4. Check doctor exists
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

        # ✅ 5. Fetch slots
        slots = TimeSlot.objects.filter(doctor=doctor).order_by('start_time')

        # ✅ 6. Build slot data with availability
        data = []
        for slot in slots:
            is_booked = Appointment.objects.filter(
                doctor=doctor,
                slot=slot,
                date=appointment_date
            ).exists()

            data.append({
                "slot_id": slot.id,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "availability": not is_booked,
                "remarks": "Booked" if is_booked else "Available"
            })

        return Response({
            "doctor": getattr(doctor, "full_name", doctor.full_name),  # support both field names
            "date": requested_date,
            "slots": data
        }, status=status.HTTP_200_OK)

    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AppointmentSerializer

class AppointmentBookingView(APIView):
    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Appointment booked successfully!", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PetBookingListView(APIView):
    """
    GET /user/bookings/?pet_id=<id>
    Returns all bookings for a given pet (past + upcoming).
    """

    def get(self, request):
        pet_id = request.query_params.get('pet_id')

        # ✅ Validate pet_id
        if not pet_id:
            return Response({"error": "pet_id query parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if pet exists
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # ✅ Get all appointments for the pet
        appointments = Appointment.objects.filter(pet=pet).order_by('-date', '-created_at')

        # ✅ Return formatted data
        serializer = AppointmentSerializer(appointments, many=True)
        return Response({
            "pet_name": pet.name,
            "total_bookings": appointments.count(),
            "bookings": serializer.data
        }, status=status.HTTP_200_OK)
        
        
class ReorderAPIView(APIView):
    """
    POST /user/reorder/
    Body: {"order_id": <int>}
    Creates a new order with the same products, quantities, and prices as a previous order.
    """

    def post(self, request):
        order_id = request.data.get('order_id')

        # ✅ 1. Validate input
        if not order_id:
            return Response({"error": "order_id is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ 2. Fetch old order
        try:
            old_order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # ✅ 3. Create new order
        new_order = Order.objects.create(
            user=old_order.user,
            status='pending',
            total_amount=0.00,  # will update later
            estimated_delivery_date=datetime.now() + timedelta(days=3)  # example logic
        )

        # ✅ 4. Copy all order items
        old_items = OrderItem.objects.filter(order=old_order)
        total_amount = 0

        for item in old_items:
            total_amount += float(item.total_price)
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product_price,
                total_price=item.total_price
            )

        # ✅ 5. Update total amount
        new_order.total_amount = total_amount
        new_order.save(update_fields=['total_amount'])

        # ✅ 6. Response
        return Response({
            "success": True,
            "message": "Reorder placed successfully.",
            "new_order_id": new_order.id,
            "total_items": old_items.count(),
            "total_amount": str(new_order.total_amount),
            "estimated_delivery_date": new_order.estimated_delivery_date.strftime("%Y-%m-%d %H:%M:%S")
        }, status=status.HTTP_201_CREATED)