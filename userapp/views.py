from xml.parsers.expat import errors
from django.shortcuts import get_object_or_404, render,redirect
from .models import *
from adminapp.models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status,viewsets,generics
from rest_framework.views import APIView
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from math import radians, sin, cos, sqrt, atan2
from doctorapp.models import Prescription


# Create your views here.
# class UserRegistrationView(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     http_method_names = ['post']
    
#     def create(self, request, *args, **kwargs):
#         serializer =self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             self.perform_create(serializer)
#             response_data = {
#                 "status":"success",
#                 "message" : "User Created Successfully",
#                 "data" : serializer.data
#             }
#             return Response(response_data, status=status.HTTP_201_CREATED)
#         else:
#             response_data = {
#                 "status":"failed",
#                 "message": "Invalid Details",
#                 "errors": serializer.errors,
#                 "data": request.data
#             }
#             return Response(response_data,status=status.HTTP_400_BAD_REQUEST)

def get_next_vaccine_for_pet(pet):
    """
    Calculate the next vaccine for a pet based on:
    1. Pet's current age
    2. Already given vaccines
    3. Vaccine schedule
    4. Annual revaccinations
    """
    from datetime import date, timedelta
    from adminapp.models import Vaccine
    from userapp.models import Appointment
    
    if not pet or not pet.birth_date:
        return None
    
    today = date.today()
    
    # Get all vaccines for this pet's subcategory
    available_vaccines = Vaccine.objects.filter(
        subcategory=pet.sub_category
    ).order_by('recommended_age')
    
    # Get already given vaccines with dates
    given_appointments = Appointment.objects.filter(
        pet=pet, 
        reason="Vaccine",
        vaccine__isnull=False,
        status__in=['booked', 'payment_completed', 'completed']
    ).select_related('vaccine').order_by('-date')
    
    # For annual revaccination, only consider PAST appointments
    past_given_appointments = given_appointments.filter(date__lte=today)
    
    given_vaccine_ids = list(given_appointments.values_list('vaccine_id', flat=True))
    
    # Helper: Parse age string to weeks
    def parse_age_to_weeks(age_str):
        age_str = str(age_str).lower()
        
        # Extract numbers
        import re
        numbers = re.findall(r'\d+', age_str)
        if not numbers:
            return 0
        
        num = int(numbers[0])
        
        if 'week' in age_str:
            return num
        elif 'month' in age_str:
            return num * 4  # Approx: 1 month = 4 weeks
        elif 'day' in age_str:
            return num // 7  # Convert days to weeks
        elif 'year' in age_str:
            return num * 52  # 1 year = 52 weeks
        else:
            # Default assumption for formats like "4 months of age"
            if 'month' in age_str:
                return num * 4
            return 0
    
    # Calculate pet's age
    age_days = (today - pet.birth_date).days
    age_weeks = age_days // 7
    age_years = age_days // 365
    
    # Check if pet is adult (more than 1 year old)
    is_adult = age_years >= 1
    
    if is_adult:
        # ADULT PET LOGIC: Focus on annual revaccinations
        
        # 1. First, check for annual revaccinations needed
        annual_vaccines = available_vaccines.filter(annual_revaccination=True)
        
        for vaccine in annual_vaccines:
            # Find when this vaccine was last given (PAST appointments only)
            last_given = past_given_appointments.filter(vaccine_id=vaccine.id).first()
            
            if last_given:
                # Check if it's been more than 1 year
                days_since_last = (today - last_given.date).days
                if days_since_last >= 365:
                    return vaccine
            else:
                # Vaccine never given to this adult pet
                # Check if it's an adult-appropriate vaccine (not puppy-only)
                vaccine_age_weeks = parse_age_to_weeks(vaccine.recommended_age)
                if vaccine_age_weeks <= 52:  # 1 year or less
                    # Puppy vaccine, adult probably doesn't need it
                    continue
                return vaccine
        
        for vaccine in available_vaccines:
            if vaccine.id not in given_vaccine_ids:
                vaccine_age_weeks = parse_age_to_weeks(vaccine.recommended_age)
                
                # Skip puppy vaccines for adults
                if vaccine_age_weeks < 24:
                    continue
                    
                if vaccine_age_weeks <= age_weeks:
                    return vaccine
                
                # 3. No vaccines needed for adult
                return None
        
    else:
        # PUPPY/KITTEN LOGIC: Follow age-based schedule
        # First, find ALL vaccines the pet hasn't taken yet
        vaccines_not_taken = []
        for vaccine in available_vaccines:
            if vaccine.id not in given_vaccine_ids:
                vaccine_age_weeks = parse_age_to_weeks(vaccine.recommended_age)
                vaccines_not_taken.append((vaccine, vaccine_age_weeks))
        
        # Sort by recommended age (weeks)
        vaccines_not_taken.sort(key=lambda x: x[1])
        
        # Return the first vaccine the pet is eligible for OR the first one in schedule
        for vaccine, vaccine_age_weeks in vaccines_not_taken:
            if age_weeks >= vaccine_age_weeks:
                return vaccine
        
        # If no vaccines are eligible yet, return the first one in schedule
        if vaccines_not_taken:
            return vaccines_not_taken[0][0]  # Return earliest vaccine
    
    # STRATEGY 2: Check for annual revaccinations
    annual_vaccines = available_vaccines.filter(annual_revaccination=True)
    
    for vaccine in annual_vaccines:
        # Find when this vaccine was last given
        last_given = given_appointments.filter(vaccine_id=vaccine.id).first()
        
        if last_given:
            # Check if it's been more than 1 year
            days_since_last = (today - last_given.date).days
            if days_since_last >= 365:
                return vaccine
    
    # No next vaccine found
    return None

class UserRegistrationView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post']
    
    def create(self, request, *args, **kwargs):

        # ✅ Check duplicate email
        email = request.data.get("email")
        if email and User.objects.filter(email=email).exists():
            return Response({
                "status": "failed",
                "message": "Email already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "message": "User Created Successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "failed",
            "message": "Invalid Details",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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
    
class DeletePetView(generics.DestroyAPIView):
    def delete(self, request):
        pet_id = request.data.get('pet_id')
        
        if not pet_id:
            return Response({'error': 'pet_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Decrement user's pet count
        user = pet.user
        if user.number_of_pets > 0:
            user.number_of_pets -= 1
            user.save(update_fields=['number_of_pets'])
        
        pet.delete()
        
        return Response({
            'message': 'Pet deleted successfully',
            'remaining_pets': user.number_of_pets
        }, status=status.HTTP_200_OK)
    
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
            return Response({'error': 'No items in the cart'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize data
        serializer = CartSerializer(cart_items, many=True)

        # Calculate total price of all items
        total_cart_price = sum(item.total_price for item in cart_items)

        return Response({
            'success': True,
            'count': len(serializer.data),
            'total_price': total_cart_price,
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

# class MakePurchaseView(APIView):
#     def post(self, request):
#         user_id = request.data.get('user_id')

#         # Validate user
#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

#         # Fetch all cart items for this user
#         cart_items = Cart.objects.filter(user=user)
#         if not cart_items.exists():
#             return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

#         # Calculate total amount
#         total_amount = sum(item.total_price for item in cart_items)

#         # Create new order
#         order = Order.objects.create(
#             user=user,
#             total_amount=total_amount,
#             status='pending',
#             estimated_delivery_date=timezone.now() + timedelta(days=5)
#         )

#         # Move cart items to OrderItem
#         for item in cart_items:
#             OrderItem.objects.create(
#                 order=order,
#                 product=item.product,
#                 quantity=item.quantity,
#                 product_price=item.product.price,
#                 total_price=item.total_price
#             )

#         # Clear cart after successful order
#         cart_items.delete()

#         # Success response
#         return Response({
#             'success': True,
#             'message': 'Order placed successfully!',
#             'order_id': order.id,
#             'amount_to_pay': str(total_amount),
#             'estimated_delivery_date': order.estimated_delivery_date.strftime('%Y-%m-%d'),
#         }, status=status.HTTP_201_CREATED)
        
class MakePurchaseView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')

        # Validate user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all cart items
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total amount
        total_amount = sum(item.total_price for item in cart_items)

        # Create new order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            status='pending'
        )

        # Calculate estimated delivery date (5 days from order_date)
        order.estimated_delivery_date = order.order_date + timedelta(days=5)
        order.save()

        # Move cart items to OrderItem
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,
                total_price=item.total_price
            )

        # Clear cart after order
        cart_items.delete()

        return Response({
            'success': True,
            'message': 'Order placed successfully!',
            'order_id': order.id,
            'amount_to_pay': str(total_amount),
            'estimated_delivery_date': order.estimated_delivery_date.strftime('%Y-%m-%d'),
        }, status=status.HTTP_201_CREATED)
        
        
# class BuyNowView(APIView):
#     def post(self, request):
#         user_id = request.data.get('user_id')
#         product_id = request.data.get('product_id')

#         if not user_id or not product_id:
#             return Response({'error': 'user_id and product_id are required'}, status=status.HTTP_400_BAD_REQUEST)

#         # Validate user
#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

#         # Validate product
#         try:
#             product = Product.objects.get(id=product_id)
#         except Product.DoesNotExist:
#             return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

#         # Check if product already in user's cart
#         cart_item, created = Cart.objects.get_or_create(
#             user=user,
#             product=product,
#             defaults={'quantity': 1, 'total_price': product.price}
#         )

#         # If exists, increment quantity
#         if not created:
#             cart_item.quantity += 1
#             cart_item.total_price = cart_item.quantity * product.price
#             cart_item.save()

#         # Create order
#         order = Order.objects.create(
#             user=user,
#             total_amount=cart_item.total_price,
#             status='pending',
#             estimated_delivery_date=timezone.now() + timedelta(days=5)
#         )

#         # Create order item
#         OrderItem.objects.create(
#             order=order,
#             product=product,
#             quantity=cart_item.quantity,
#             product_price=product.price,
#             total_price=cart_item.total_price
#         )

#         # Remove item from cart after purchase
#         cart_item.delete()

#         return Response({
#             'success': True,
#             'message': 'Product purchased successfully!',
#             'order_id': order.id,
#             'amount_to_pay': str(order.total_amount),
#             'estimated_delivery_date': order.estimated_delivery_date.strftime('%Y-%m-%d')
#         }, status=status.HTTP_201_CREATED)


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

        # Add or update cart item
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': 1, 'total_price': product.price}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.total_price = cart_item.quantity * product.price
            cart_item.save()

        # Create new order
        order = Order.objects.create(
            user=user,
            total_amount=cart_item.total_price,
            status='pending'
        )

        # Estimated delivery = 5 days after order_date
        order.estimated_delivery_date = order.order_date + timedelta(days=5)
        order.save()

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
    
    # Validate email address
    user_email = getattr(order.user, 'email', '')
    if not user_email or '@' not in user_email:
        print(f"WARNING: Invalid email for user {order.user.id}, skipping email")
        return
    
    # Send email
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],  # ✅ Send only to the user
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

        appointment_id = request.data.get('appointment_id')
        order_id = request.data.get('order_id')

        # Determine payment_for
        if appointment_id:
            data["payment_for"] = "appointment"
        elif order_id:
            data["payment_for"] = "order"

        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()

            # Validate amount based on type
            if appointment_id:
                # For appointment payment - update appointment status
                appointment = get_object_or_404(Appointment, id=appointment_id, pet__user_id=payment.user.id)
                appointment.status = 'payment_completed'
                payment.appointment = appointment #Writing the appointment ticket number(left) on the receipt (RHS)
                payment.save(update_fields=['appointment'])
                appointment.save()
                target_amount = appointment.fee_amount
            
            elif order_id:
                order = get_object_or_404(Order, id=order_id, user_id=payment.user.id)
                target_amount = order.total_amount
            
            else:
                return Response({"error": "Either appointment_id or order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate amount
            if payment.amount != target_amount:
                payment.payment_status = 'failed'
                payment.save()
                return Response({"error": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)

            #Payment successful
            payment.payment_status = "success"
            payment.save()

            # Handle order-specific logic
            if order_id:
                order.status = "order placed"
                order.estimated_delivery_date = timezone.now() + timedelta(days=5)
                order.save()
                reduce_stock_after_payment(order)
                send_order_confirmation_email(order, payment)

            response_data = {
                "message": "UPI payment successful",
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "for": "appointment" if appointment_id else "order",
            }
            
            if appointment_id:
                response_data["appointment_id"] = appointment_id
            else:
                response_data["order_id"] = order_id
            
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from datetime import datetime
import re                                       # Add this import for card validation

class CardPaymentView(APIView):                 #Handles Card Payment

    def validate_card_data(self, data):         #Validate card details
        errors = {}
        
        # Cardholder name validation
        if not data.get('cardholder_name') or len(data['cardholder_name'].strip()) < 2:
            errors['cardholder_name'] = "Valid cardholder name is required"
        
        # Card number validation (basic Luhn check)
        card_number = data.get('card_number', '').replace(' ', '')
        if not card_number.isdigit() or len(card_number) not in [15, 16]:
            errors['card_number'] = "Valid card number is required (15-16 digits)"
        
        # Expiry date validation (MM/YY format)
        expiry_date = data.get('expiry_date', '')
        if not expiry_date:  # Add this check
            errors['expiry_date'] = "Expiry date is required"
        elif not re.match(r'^(0[1-9]|1[0-2])/([0-9]{2})$', expiry_date):
            errors['expiry_date'] = "Expiry date must be in MM/YY format"
        else:
            # Check if card is expired
            month, year = expiry_date.split('/')
            current_year = datetime.now().year % 100
            current_month = datetime.now().month

            try:
                if int(year) < current_year or (int(year) == current_year and int(month) < current_month):
                    errors['expiry_date'] = "Card has expired"
            except ValueError:
                errors['expiry_date'] = "Invalid expiry date format"
        
        # CVV validation
        cvv = data.get('cvv_number', '')
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            errors['cvv_number'] = "Valid CVV is required (3-4 digits)"
        
        return errors

    def post(self, request):
        data = request.data.copy()  # Use copy to avoid mutating request.data
        data["payment_method"] = "card"

        appointment_id = request.data.get('appointment_id')
        order_id = request.data.get('order_id')

        # Validate card details first
        card_errors = self.validate_card_data(data)
        if card_errors:
            return Response({"error": "Invalid card details", "details": card_errors}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Determine payment_for
        if appointment_id:
            data["payment_for"] = "appointment"
        
        elif order_id:
            data["payment_for"] = "order"
        
        else:
            return Response({"error": "Either appointment_id or order_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Make a copy of card_number before masking for validation
        original_card_number = data.get('card_number', '')

        # Mask sensitive data in request data for logging/security
        if original_card_number:
            if len(original_card_number) > 4:
                data['card_number'] = '*' * (len(original_card_number) - 4) + original_card_number[-4:]
            else:
                data['card_number'] = original_card_number  # Keep as is if too short

        # Create a copy of data for serializer with original card number
        serializer_data = request.data.copy()  # ← Copy from ORIGINAL request data
        serializer_data["payment_method"] = "card"
        serializer_data["payment_for"] = "appointment" if appointment_id else "order"

        serializer = PaymentSerializer(data=serializer_data)
        if serializer.is_valid():
            payment = serializer.save()

            # Validate amount based on type
            if appointment_id:
                appointment = get_object_or_404(Appointment, id=appointment_id, pet__user_id=payment.user.id)
                payment.appointment = appointment
                payment.save(update_fields=['appointment'])
                appointment.status = 'payment_completed'
                appointment.save()
                target_amount = appointment.fee_amount
            
            elif order_id:
                order = get_object_or_404(Order, id=order_id, user_id=payment.user.id)
                target_amount = order.total_amount

            # Validate amount
            if payment.amount != target_amount:
                payment.payment_status = 'failed'
                payment.save()
                return Response({"error": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)

            # Log the payment details for debugging
            print(f"Payment attempt - User: {payment.user.id}, Amount: {payment.amount}, Card ending: {original_card_number[-4:] if original_card_number else 'N/A'}")

            # Simulate payment processing
            # In real implementation, integrate with payment gateway here
            try:
                # Validate amount matches
                if payment.amount != target_amount:
                    raise Exception(f"Amount mismatch. Payment: {payment.amount}, Expected: {target_amount}")

                # Check for test card numbers
                test_cards = ['4111111111111111', '4242424242424242', '5555555555554444']
                if original_card_number in test_cards:
                    print("Test card detected - simulating successful payment")
                # Simulate payment processing delay
                # payment_gateway_response = process_card_payment(payment)
                # if not payment_gateway_response.success:
                # raise Exception("Payment gateway declined")
                
                payment.payment_status = "success"
                payment.save()

                # Handle order-specific logic
                if order_id:
                    order.status = "order placed"
                    order.estimated_delivery_date = timezone.now() + timedelta(days=5)
                    order.save()
                    reduce_stock_after_payment(order)
                    send_order_confirmation_email(order, payment)

                # Prepare response data
                response_data = {
                    "message": "Card payment successful",
                    "payment_id": payment.id,
                    "amount": str(payment.amount),
                    "for": "appointment" if appointment_id else "order",
                    "payment_method": "card",
                    "last_four_digits": payment.card_number[-4:] if payment.card_number else None,
                    "cardholder_name": payment.cardholder_name,
                    "transaction_date": payment.payment_date.isoformat()
                }

                # Add the correct ID field
                if appointment_id:
                    response_data["appointment_id"] = appointment_id
                else:
                    response_data["order_id"] = order_id

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                # Handle payment processing failure
                payment.payment_status = "failed"
                payment.save()
                # Log the actual error for debugging
                import traceback
                print("="*50)
                print(f"CARD PAYMENT ERROR: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                print("Traceback:")
                traceback.print_exc()
                print("="*50)
                return Response({"error": "Payment processing failed. Please check your card details and try again."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.core.mail import EmailMultiAlternatives

class CancelOrderView(APIView):       #Allows user to cancel an order without authentication

    authentication_classes = []       # Disable authentication
    permission_classes = []           # Disable permission checks

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
        subject = f"Your Order #{order.id} Has Been Cancelled"
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
            {"status": "succuss", "message": "Order cancelled and email sent."},
            status = status.HTTP_200_OK
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
            # Check if doctor has at least one available slot
            has_available_slots = TimeSlot.objects.filter(
                doctor=doctor,
                is_available=True
            ).exists()
            
            if not has_available_slots:
                continue  # Skip doctors with no available slots
                
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
                    "image": f"media/{doctor.image.name}" if doctor.image else None,
                    "id_card": f"media/{doctor.id_card.name}" if doctor.id_card else None,
                    "distance_km": round(distance, 2),
                    "has_available_slots": True
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
    GET /user/view_slots/?doctor_id=<id>&date=YYYY-MM-DD
    Returns all slots for the doctor with availability for that date.
    Checks both booking count and doctor-cancelled slots.
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

        # ✅ 5. Get current time in local timezone (Asia/Kolkata)
        from django.utils import timezone
        import pytz
        
        # Get current time in UTC
        now_utc = timezone.now()
        
        # Convert to Asia/Kolkata timezone
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        now_kolkata = now_utc.astimezone(kolkata_tz)
        
        current_time = now_kolkata.time()
        today_date = now_kolkata.date()
        
        # ✅ 6. Import CancelledSlot model from doctorapp
        from doctorapp.models import CancelledSlot
        
        # ✅ 7. Fetch slots
        slots = TimeSlot.objects.filter(doctor=doctor).order_by('start_time')

        # ✅ 8. Build slot data with availability
        data = []
        for slot in slots:
            # Skip slots that have already passed for today
            if appointment_date == today_date:
                if slot.start_time <= current_time:
                    continue  # Skip past slots for today
            
            # Check if this slot is cancelled by doctor for this specific date
            is_cancelled_by_doctor = CancelledSlot.objects.filter(
                doctor=doctor,
                slot=slot,
                date=appointment_date
            ).exists()
            
            print(f"DEBUG - User View - Doctor: {doctor.id}, Slot: {slot.id}, Date: {appointment_date}, Cancelled: {is_cancelled_by_doctor}")
            
            # Count non-cancelled appointments for this slot on this date
            booked_count = Appointment.objects.filter(
                doctor=doctor,
                slot=slot,
                date=appointment_date
            ).exclude(status='cancelled').count()
            
            # Check if slot is available:
            # 1. Must NOT be cancelled by doctor
            # 2. Must have less than 4 bookings (max 4 per 15-min slot)
            if is_cancelled_by_doctor:
                is_available = False
                remarks = "Unavailable (Doctor cancelled this slot for this date)"
            else:
                is_available = booked_count < 4
                remarks = "Fully Booked" if not is_available else f"Available ({4 - booked_count} seats left)"
            
            data.append({
                "slot_id": slot.id,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "availability": is_available,
                "booked_count": booked_count,
                "cancelled_by_doctor": is_cancelled_by_doctor,
                "remarks": remarks
            })

        return Response({
            "doctor": doctor.full_name,
            "date": requested_date,
            "slots": data
        }, status=status.HTTP_200_OK)

    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AppointmentSerializer

class AppointmentBookingView(APIView):
    def post(self, request):
        # Additional validation before serializer
        reason = request.data.get('reason')
        vaccine_id = request.data.get('vaccine')
        
        if reason == "Vaccine" and not vaccine_id:
            return Response({
                "error": "vaccine_id is required when reason is 'Vaccine'",
                "message": "Please select a vaccine from the vaccine list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if slot is available (not cancelled by doctor for this date)
        slot_id = request.data.get('slot')
        doctor_id = request.data.get('doctor')
        appointment_date = request.data.get('date')
        
        if slot_id and doctor_id and appointment_date:
            try:
                # Parse date
                from datetime import datetime
                booking_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                
                # Check if slot exists
                slot = TimeSlot.objects.get(id=slot_id, doctor_id=doctor_id)
                
                # Check if this slot is cancelled by doctor for this specific date
                from doctorapp.models import CancelledSlot
                is_cancelled = CancelledSlot.objects.filter(
                    doctor_id=doctor_id,
                    slot_id=slot_id,
                    date=booking_date
                ).exists()
                
                if is_cancelled:
                    return Response(
                        {"error": "This slot has been cancelled by the doctor for this date and is not available for booking."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except TimeSlot.DoesNotExist:
                return Response(
                    {"error": "Invalid slot or doctor combination."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Appointment booked successfully!", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CancelAppointmentView(APIView):
    def patch(self, request):
        appointment_id = request.data.get('appointment_id')
        
        if not appointment_id:
            return Response({'error': 'appointment_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Check time restriction before updating
        from django.utils import timezone
        from datetime import datetime
        import pytz
        
        local_tz = pytz.timezone('Asia/Kolkata')
        now_local = timezone.now().astimezone(local_tz)
        
        appointment_datetime_local = local_tz.localize(
            datetime.combine(appointment.date, appointment.slot.start_time)
        )
        
        time_difference = appointment_datetime_local - now_local
        
        # 3 hours = 10800 seconds
        if time_difference.total_seconds() < 10800:
            return Response({
                'error': 'Appointments can only be cancelled at least 3 hours before the scheduled time.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status to cancelled
        appointment.status = 'cancelled'
        appointment.save()
        
        return Response({
            'message': 'Appointment cancelled successfully',
            'appointment_id': appointment.id,
            'status': appointment.status
        }, status=status.HTTP_200_OK)

# class VaccineBookingView(APIView):
#     """
#     Simplified vaccine-only booking
#     Input: pet_id, vaccine_id, preferred_date
#     Output: Auto-assigned doctor, slot, and appointment
#     """
    
#     def post(self, request):
#         pet_id = request.data.get('pet_id')
#         vaccine_id = request.data.get('vaccine_id')
#         preferred_date = request.data.get('preferred_date')
        
#         # Validate required fields
#         if not all([pet_id, vaccine_id, preferred_date]):
#             return Response({'error': 'pet_id, vaccine_id, and preferred_date are required'},
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             pet = Pet.objects.get(id=pet_id)
#             vaccine = Vaccine.objects.get(id=vaccine_id)
#         except (Pet.DoesNotExist, Vaccine.DoesNotExist):
#             return Response({'error': 'Invalid pet or vaccine ID'},
#                           status=status.HTTP_400_BAD_REQUEST)

#         # Check if pet's subcategory is in allowed list
#         allowed_subcategories = ['Dog', 'Cat', 'Poultry', 'Cattle', 'Sheep', 'Goat', 'Swine']
#         if pet.sub_category.petsubcategory not in allowed_subcategories:
#             return Response({
#                 'error': 'Vaccine not available for this pet type',
#                 'pet_subcategory': pet.sub_category.petsubcategory,
#                 'allowed_subcategories': allowed_subcategories
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Special case: Sheep and Goat can use Cattle vaccines
#         if pet.sub_category.petsubcategory in ['Sheep', 'Goat']:
#             cattle_sub = PetSubcategory.objects.get(petsubcategory='Cattle')
#             if vaccine.subcategory != cattle_sub:
#                 return Response({
#                     'error': 'This vaccine is not available for this pet type',
#                     'pet_subcategory': pet.sub_category.petsubcategory,
#                     'vaccine_subcategory': vaccine.subcategory.petsubcategory,
#                     'note': 'Sheep and Goat can use Cattle vaccines'
#                 }, status=status.HTTP_400_BAD_REQUEST)
        
#         else:
#             # For other pets, vaccine must match their subcategory
#             if vaccine.subcategory != pet.sub_category:
#                 return Response({
#                     'error': 'This vaccine is not available for this pet type',
#                     'pet_subcategory': pet.sub_category.petsubcategory,
#                     'vaccine_subcategory': vaccine.subcategory.petsubcategory
#                 }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Find available doctor (currently all doctors handle all pet types)
#         # TODO: Add doctor specialization field later
#         doctors = Doctor.objects.filter(is_approved=True)
#         if not doctors.exists():
#             return Response({'error': 'No doctors available'},
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         # For now, pick first available doctor
#         # Later: Filter doctors by pet type specialization
#         doctor = doctors.first()
        
#         # Find available slot for preferred date
#         try:
#             appointment_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
#         except ValueError:
#             return Response({'error': 'Invalid date format. Use YYYY-MM-DD'},
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         # Find available slot (simplified: first available slot)
#         slots = TimeSlot.objects.filter(
#             doctor=doctor,
#             is_available=True
#         ).order_by('start_time')
        
#         if not slots.exists():
#             return Response({'error': 'No available slots for selected date'},
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         slot = slots.first()
        
#         # Create appointment
#         appointment = Appointment.objects.create(
#             pet=pet,
#             doctor=doctor,
#             date=appointment_date,
#             slot=slot,
#             appointment_type='clinical',
#             reason='Vaccine',
#             vaccine=vaccine,
#             fee_amount=100.00,
#             status='booked'
#         )
        
#         serializer = AppointmentSerializer(appointment)
        
#         return Response({
#             'message': 'Vaccine booked successfully',
#             'appointment': serializer.data
#         }, status=status.HTTP_201_CREATED)

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
        serializer = AppointmentsSerializer(appointments, many=True)
        
        # Calculate next vaccine
        next_vaccine = get_next_vaccine_for_pet(pet)
        
        response_data = {
            "pet_name": pet.name,
            "total_bookings": appointments.count(),
            "bookings": serializer.data
        }
        
        # Add next vaccine info if available
        if next_vaccine:

            # Check if this is an annual revaccination
            
            is_annual = False
            
            from datetime import date
            today = date.today()
            
            # First, check if pet has had this vaccine before
            past_vaccine_exists = Appointment.objects.filter(
                pet=pet,
                vaccine=next_vaccine,
                date__lte=today,
                status__in=['booked', 'payment_completed', 'completed']
            ).exists()
            
            # If pet has had it before AND vaccine requires annual revaccination
            if past_vaccine_exists and next_vaccine.annual_revaccination:
                is_annual = True
            
            # Determine note
            if is_annual:
                note = "Annual revaccination due"
            elif "week" in next_vaccine.recommended_age.lower() and "year" in pet.get_age().lower():
                note = "Catch-up vaccine (missed earlier schedule)"
            else:
                note = "Next scheduled vaccine"
            
            response_data["next_vaccine"] = {
                "vaccine_id": next_vaccine.id,
                "vaccine_name": next_vaccine.vaccine_name,
                "recommended_age": next_vaccine.recommended_age,
                "disease_protected": next_vaccine.disease_protected,
                "pet_current_age": pet.get_age(),
                "is_annual_revaccination": is_annual,
                "note": "Annual revaccination due" if is_annual else "Next scheduled vaccine"
            }
        else:
            response_data["next_vaccine"] = None
        
        return Response(response_data, status=status.HTTP_200_OK)
        

class BookingDetailsAPIView(APIView):
    """
    GET /appointments/detail/?booking_id=<id>
    """

    def get(self, request):
        booking_id = request.query_params.get('booking_id')
        if not booking_id:
            return Response(
                {"success": False, "message": "booking_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = get_object_or_404(
            Appointment.objects.select_related('pet', 'doctor', 'slot'),
            id=booking_id
        )

        serializer = AppointmentsSerializer(appointment)
        data = serializer.data

        # Add booleans in VIEW
        data["has_feedback"] = appointment.feedback_set.exists()
        data["has_complaint"] = appointment.complaint_set.exists()

        return Response({
            "success": True,
            "message": "Booking details fetched successfully",
            "data": data
        }, status=status.HTTP_200_OK)

class VaccineListView(APIView):
    def get(self, request):
        pet_id = request.query_params.get('pet_id')
        
        if not pet_id:
            return Response({'error': 'pet_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Check if pet's subcategory is in allowed list
        allowed_subcategories = ['Dog', 'Cat', 'Poultry', 'Cattle', 'Sheep', 'Goat', 'Swine']
        if pet.sub_category.petsubcategory not in allowed_subcategories:
            return Response({
                'error': 'Vaccine not available for this pet type',
                'pet_subcategory': pet.sub_category.petsubcategory,
                'allowed_subcategories': allowed_subcategories
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Special case: Sheep and Goat share vaccines with Cattle
        if pet.sub_category.petsubcategory in ['Sheep', 'Goat']:
            cattle_sub = PetSubcategory.objects.get(petsubcategory='Cattle')
            vaccines = Vaccine.objects.filter(subcategory=cattle_sub)
        else:
            # Filter vaccines by pet's subcategory
            vaccines = Vaccine.objects.filter(subcategory=pet.sub_category)
        
        # Parse pet age for recommendations
        pet_age_weeks = None
        if pet.birth_date:
            from datetime import date
            today = date.today()
            age_days = (today - pet.birth_date).days
            pet_age_weeks = age_days // 7
            
        # Serialize with recommendation flag
        vaccine_data = []
        for vaccine in vaccines:
            vaccine_dict = VaccineSerializer(vaccine).data
            
            # Basic recommendation logic
            if pet_age_weeks:
                # Parse vaccine recommended age (simplified)
                rec_age = vaccine.recommended_age.lower()
                if 'week' in rec_age:
                    try:
                        weeks_needed = int(''.join(filter(str.isdigit, rec_age.split()[0])))
                        vaccine_dict['is_recommended'] = pet_age_weeks >= weeks_needed
                    except:
                        vaccine_dict['is_recommended'] = False
                elif 'month' in rec_age:
                    try:
                        months_needed = int(''.join(filter(str.isdigit, rec_age.split()[0])))
                        # Convert pet age to months
                        pet_age_months = pet_age_weeks // 4
                        vaccine_dict['is_recommended'] = pet_age_months >= months_needed
                    except:
                        vaccine_dict['is_recommended'] = False
                else:
                    vaccine_dict['is_recommended'] = True  # For adult vaccines
            else:
                vaccine_dict['is_recommended'] = None
            
            vaccine_data.append(vaccine_dict)
        
        response_data = {
            'pet_id': pet_id,
            'pet_subcategory': pet.sub_category.petsubcategory,
            'count': len(vaccine_data),
            'vaccines': vaccine_data,
            'pet_info': {
                'id': pet.id,
                'name': pet.name,
                'sub_category': pet.sub_category.petsubcategory,
                'age': pet.get_age()
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
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
        
    
import os
from pathlib import Path
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response
import google.generativeai as genai


# -----------------------------------------------------------
# Load .env only here (NOT in settings.py)
# -----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Go up one more level
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Debug print (masked)
#print("Loaded GOOGLE_API_KEY:", GOOGLE_API_KEY)
print("Loaded GOOGLE_API_KEY:", GOOGLE_API_KEY if GOOGLE_API_KEY else "NOT FOUND")
print("ENV_PATH:", ENV_PATH)
print("File exists:", os.path.exists(ENV_PATH))


# -----------------------------------------------------------
# Configure Gemini globally
# -----------------------------------------------------------
genai.configure(api_key=GOOGLE_API_KEY)


# -----------------------------------------------------------
# Allowed keywords for pet health
# -----------------------------------------------------------
PET_KEYWORDS = [
    "pet health", "well-being", "veterinary", "vet", "clinic", "checkup",
    "diagnosis", "treatment", "medicine", "medication", "first aid",
    "infection", "disease", "allergy", "symptoms", "conditions",
    "vaccination", "immunization", "deworming", "flea", "ticks",
    "parasites", "mites", "lice", "rabies", "distemper", "parvo",

    "skin", "coat", "fur", "paws", "ears", "eyes", "nose", "teeth",
    "gums", "tail", "claws", "nails", "stomach", "digestive system",
    "respiratory", "heart", "lungs", "kidney", "liver", "joints",
    "bones", "muscles",

    "vomiting", "diarrhea", "coughing", "sneezing", "fever", "itching",
    "hair loss", "shedding", "wounds", "injury", "pain", "swelling",
    "dehydration", "obesity", "arthritis", "diabetes", "heatstroke",
    "urinary infection", "ear infection", "eye infection", "skin infection",

    "dog", "cat", "puppy", "kitten", "bird", "rabbit", "hamster",
    "fish", "turtle", "parrot",

    "diet", "nutrition", "food", "meal", "treats", "hydration",
    "water intake", "supplements", "vitamins", "protein",
    "homemade food", "digestive issues",

    "anxiety", "stress", "aggression", "fear", "training",
    "behavior issues", "lethargy", "hyperactive", "sleeping habits",

    "neutering", "spaying", "pregnancy", "heat cycle", "mating",
    "breeding", "lactation", "newborn care",

    "bathing", "cleaning", "grooming", "nail trim", "ear cleaning",
    "teeth cleaning", "hygiene",

    "not eating", "not drinking", "difficulty breathing", "collapse",
    "bleeding", "seizure", "choking", "poisoning", "accident",
    "emergency",

    "hello", "hi", "hey", "help", "query", "question", "advice",
    "tips", "guidance", "support"
]



def is_pet_related(text):
    """Check if message is pet related."""
    text = text.lower()
    return any(keyword in text for keyword in PET_KEYWORDS)


# -----------------------------------------------------------
# Chatbot API View
# -----------------------------------------------------------

class PetChatAPIView(APIView):

    def post(self, request):
        user_message = request.data.get("message")

        if not user_message:
            return Response({"error": "Message is required"}, status=400)

        # Filter unrelated topics
        if not is_pet_related(user_message):
            return Response({
                "reply": "❗ I can only answer questions related to pet health."
            })

        try:
            prompt = (
                "You are a Pet Health Expert. Only answer questions related to "
                "pets, symptoms, diseases, vaccination, grooming, diet, or safety.\n\n"
                f"User: {user_message}"
            )

            # Use a global region model → avoids quota issues
            model = genai.GenerativeModel("gemini-2.5-flash")

            response = model.generate_content(prompt)

            return Response({"reply": response.text})

        except Exception as e:
            return Response({
                "error": f"Gemini error: {str(e)}"
            }, status=500)


class PetFoodRecommendationAPIView(APIView):

    def get(self, request):
        return Response({"message": "Use POST method for recommendations."})

    def post(self, request):
        pet_id = request.data.get("pet_id")

        if not pet_id:
            return Response(
                {"error": "pet_id is required."},
                status=400
            )

        try:
            pet = Pet.objects.get(id=pet_id)

        except Pet.DoesNotExist:
            return Response(
                {"error": "Pet not found."},
                status=404
            )

        breed = pet.sub_category.petsubcategory  # Or appropriate breed field
        age = pet.get_age()

        # Extract numeric age from string (e.g., "3 years" -> 3)
        age_str = str(pet.get_age())
        print(f"DEBUG - Original age string: {age_str}")
        age_years = 1  # Default if parsing fails
        age_months = 0  # Initialize months variable

        try:
            import re
            
            # Check for years first
            year_match = re.search(r'(\d+)\s*years?', age_str)
            if year_match:
                age_years = int(year_match.group(1))
                age_months = 0
                print(f"DEBUG - Found years: {age_years}")
            
            # Check for months
            elif re.search(r'month', age_str):
                month_match = re.search(r'(\d+)\s*months?', age_str)
                if month_match:
                    age_months = int(month_match.group(1))
                    age_years = 0
                    print(f"DEBUG - Found months: {age_months}, setting age_years=0")
            
            # Check for weeks
            elif re.search(r'week', age_str):
                week_match = re.search(r'(\d+)\s*weeks?', age_str)
                if week_match:
                    age_years = 0
                    age_months = 0
                    print(f"DEBUG - Found weeks, setting age_years=0")
            
            # If no patterns match, keep defaults
            else:
                print(f"DEBUG - No age pattern matched, keeping defaults")
                
        except Exception as e:
            age_years = 1
            age_months = 0
            print(f"DEBUG - Exception caught: {e}, setting age_years=1")
            
        print(f"DEBUG - Final values - age_years: {age_years}, age_months: {age_months}")
        health = pet.health_condition or "Generally healthy"

        # Determine age display text
        if age_years > 0:
            age_display = f"{age_years} years"
        elif age_months > 0:
            age_display = f"{age_months} months"
        else:
            age_display = "puppy/kitten (under 1 month)"
        
        prompt = f"""
        You are a professional veterinary diet planner.

        A pet has the following details:
        - Breed: {breed}
        - Age: {age_display}
        - Health Condition: {health}

        Provide the best food recommendations including:
        - Food brand suggestions
        - Portion size
        - Daily calories needed
        - Protein requirements
        - Specific food types good for this condition
        - Foods to avoid

        Reply in clear bullet points.
        """

        print(f"DEBUG - Pet Food Recommendation Request:")
        print(f"  Pet ID: {pet_id}")
        print(f"  Breed: {breed}")
        print(f"  Age: {age_years} years (original: {age})")
        print(f"  Health: {health}")

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)

            return Response({"recommendation": response.text})

        except Exception as e:
            return Response(
                {"error": f"Gemini error: {str(e)}"},
                status=500
            )


class CreateFeedbackView(APIView):
    def post(self, request):
        appointment_id = request.data.get("appointment")
        
        # Validate appointment exists
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Invalid appointment ID"
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Feedback submitted successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        

class CreateComplaintView(APIView):
    def post(self, request):
        appointment_id = request.data.get("appointment")

        # Validate appointment exists
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Invalid appointment ID"
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ComplaintSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Complaint submitted successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserFeedbackListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({
                "status": "error",
                "message": "user_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch feedback where appointment -> pet -> user matches
        feedbacks = Feedback.objects.filter(
            appointment__pet__user_id=user_id
        ).order_by('-created_at')

        serializer = FeedbackSerializer(feedbacks, many=True)

        return Response({
            "status": "success",
            "count": feedbacks.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
class UserComplaintListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({
                "status": "error",
                "message": "user_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch complaints where appointment -> pet -> user matches
        complaints = Complaint.objects.filter(
            appointment__pet__user_id=user_id
        ).order_by('-created_at')

        serializer = ComplaintSerializer(complaints, many=True)

        return Response({
            "status": "success",
            "count": complaints.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class NextVaccineRecommendationView(APIView):
    def get(self, request):
        pet_id = request.query_params.get('pet_id')
        
        if not pet_id:
            return Response({"error": "pet_id parameter is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        next_vaccine = get_next_vaccine_for_pet(pet)
        
        if next_vaccine:
            # Check if this is an annual revaccination
            is_annual = False
            today = date.today()
            
            # Check if pet has had this vaccine before (PAST appointments)
            past_vaccine_exists = Appointment.objects.filter(
                pet=pet,
                vaccine=next_vaccine,
                date__lte=today,
                status__in=['booked', 'payment_completed', 'completed']
            ).exists()
            
            # If pet has had it before AND vaccine requires annual revaccination
            if past_vaccine_exists and next_vaccine.annual_revaccination:
                is_annual = True
            
            # Determine note
            if is_annual:
                note = "Annual revaccination due"
            elif "week" in next_vaccine.recommended_age.lower() and "year" in pet.get_age().lower():
                note = "Catch-up vaccine (missed earlier schedule)"
            else:
                note = "Next scheduled vaccine"
            
            response_data = {
                "pet_id": pet.id,
                "pet_name": pet.name,
                "pet_age": pet.get_age(),
                "pet_subcategory": pet.sub_category.petsubcategory,
                "next_vaccine": {
                    "vaccine_id": next_vaccine.id,
                    "vaccine_name": next_vaccine.vaccine_name,
                    "recommended_age": next_vaccine.recommended_age,
                    "disease_protected": next_vaccine.disease_protected,
                    "annual_revaccination": next_vaccine.annual_revaccination,
                    "is_annual_revaccination": is_annual,
                    "note": note
                }
            }
        else:
            response_data = {
                "pet_id": pet.id,
                "pet_name": pet.name,
                "pet_age": pet.get_age(),
                "message": "No vaccine recommendations at this time",
                "next_vaccine": None
            }
        
        return Response(response_data, status=status.HTTP_200_OK)

class UserPrescriptionListView(APIView):
    """
    API for users to view all prescriptions for their pets
    GET: /user/prescriptions/?user_id=<id>
    Returns all prescriptions across all pets of the user
    """
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({
                "status": "error",
                "message": "user_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all pets for this user
        pets = Pet.objects.filter(user=user)
        pet_ids = pets.values_list('id', flat=True)
        
        # Get all prescriptions for these pets
        from doctorapp.models import Prescription
        prescriptions = Prescription.objects.filter(
            pet_id__in=pet_ids
        ).select_related('doctor', 'pet', 'appointment').order_by('-issued_date')
        
        # Format response data
        prescription_list = []
        for prescription in prescriptions:
            prescription_list.append({
                "id": prescription.id,
                "appointment_id": prescription.appointment.id,
                "appointment_date": prescription.appointment.date,
                "doctor_id": prescription.doctor.id,
                "doctor_name": prescription.doctor.full_name,
                "pet_id": prescription.pet.id,
                "pet_name": prescription.pet.name,
                "diagnosis": prescription.appointment.diagnosis_and_verdict,
                "medications": prescription.medications,
                "days_duration": prescription.days_duration,
                "issued_date": prescription.issued_date,
                "is_active": prescription.is_active,
                "notes": prescription.notes
            })
        
        return Response({
            "status": "success",
            "user_id": user_id,
            "count": len(prescription_list),
            "prescriptions": prescription_list
        }, status=status.HTTP_200_OK)


class UserPrescriptionDetailView(APIView):
    """
    API for users to view detailed prescription information
    GET: /user/prescription-view/?prescription_id=<id>&user_id=<id>
    Returns complete prescription details with appointment, doctor, and pet information
    """
    
    def get(self, request):
        prescription_id = request.query_params.get('prescription_id')
        user_id = request.query_params.get('user_id')
        
        # Validate required parameters
        if not prescription_id:
            return Response({
                "status": "error",
                "message": "prescription_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user_id:
            return Response({
                "status": "error",
                "message": "user_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify user exists
            user = User.objects.get(id=user_id)
            
            # Get prescription and verify it belongs to user's pet
            from doctorapp.models import Prescription
            prescription = Prescription.objects.get(id=prescription_id)
            
            # Check if this prescription's pet belongs to the user
            if prescription.pet.user.id != int(user_id):
                return Response({
                    "status": "error",
                    "message": "This prescription does not belong to any of your pets."
                }, status=status.HTTP_403_FORBIDDEN)
            
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Prescription.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Prescription not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get related data
        appointment = prescription.appointment
        doctor = prescription.doctor
        pet = prescription.pet
        
        # Build detailed response
        response_data = {
            "id": prescription.id,
            "appointment_id": appointment.id,
            "issued_date": prescription.issued_date,
            "is_active": prescription.is_active,
            "diagnosis": appointment.diagnosis_and_verdict,
            "medications": prescription.medications,
            "days_duration": prescription.days_duration,
            "notes": prescription.notes,
            "appointment_details": {
                "date": appointment.date,
                "slot": f"{appointment.slot.start_time.strftime('%H:%M')} - {appointment.slot.end_time.strftime('%H:%M')}" if appointment.slot else None,
                "type": appointment.appointment_type,
                "reason": appointment.reason,
                "symptoms": appointment.symptoms,
                "status": appointment.status
            },
            "doctor_details": {
                "id": doctor.id,
                "name": doctor.full_name,
                "email": doctor.email,
                "phone": doctor.phone_number,
                "address": doctor.address,
                "image": doctor.image.url if doctor.image else None
            },
            "pet_details": {
                "id": pet.id,
                "name": pet.name,
                "category": pet.category.petcategory if pet.category else None,
                "sub_category": pet.sub_category.petsubcategory if pet.sub_category else None,
                "gender": pet.gender,
                "age": pet.get_age(),
                "weight": pet.weight,
                "image": pet.pet_image.url if pet.pet_image else None,
                "health_condition": pet.health_condition
            }
        }
        
        return Response({
            "status": "success",
            "message": "Prescription details fetched successfully.",
            "prescription": response_data
        }, status=status.HTTP_200_OK)