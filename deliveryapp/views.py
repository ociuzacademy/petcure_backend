from django.shortcuts import get_object_or_404, render,redirect
from .models import *
from adminapp.models import *
from deliveryapp.models import *
from userapp.models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status,viewsets,generics
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import math


# Create your views here.
# class DeliveryBoyRegistrationView(viewsets.ModelViewSet):
#     queryset = DeliveryAgent.objects.all()
#     serializer_class = DeliveryBoySerializer
#     http_method_names = ['post']
    
#     def create(self, request, *args, **kwargs):
#         serializer =self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             self.perform_create(serializer)
#             response_data = {
#                 "status":"success",
#                 "message" : "Delivery Agent Created Successfully",
#                 "data" : serializer.data
#             }
#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             response_data = {
#                 "status":"failed",
#                 "message": "Invalid Details",
#                 "errors": serializer.errors,
#                 "data": request.data
#             }
#             return Response(response_data,status=status.HTTP_400_BAD_REQUEST)


class DeliveryBoyRegistrationView(viewsets.ModelViewSet):
    queryset = DeliveryAgent.objects.all()
    serializer_class = DeliveryBoySerializer
    http_method_names = ['post']
    
    def create(self, request, *args, **kwargs):

        # ✅ Check duplicate email
        email = request.data.get("email")
        if email and DeliveryAgent.objects.filter(email=email).exists():
            return Response({
                "status": "failed",
                "message": "Email already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            response_data = {
                "status": "success",
                "message": "Delivery Agent Created Successfully",
                "data": serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        else:
            response_data = {
                "status": "failed",
                "message": "Invalid Details",
                "errors": serializer.errors
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)



class DeliveryBoyLoginAPI(APIView):
    def post(self, request):
        serializer = DeliveryBoyLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            try:
                boy = DeliveryAgent.objects.get(email=email)
                # Check if delivery boy is approved
                if boy.status != 'approved':
                    return Response({"error": "Your account is not approved yet."}, status=status.HTTP_403_FORBIDDEN)
                # Check password
                if boy.password != password:
                    return Response({"error": "Invalid password."}, status=status.HTTP_401_UNAUTHORIZED)
                
                # Login successful
                return Response({
                    "id": boy.id,
                    "username": boy.username,
                    "email": boy.email,
                    "phone": boy.phone,
                    "city": boy.city,
                    "profile_image": boy.profile_image.url if boy.profile_image else None,
                    "id_card_image": boy.id_card_image.url if boy.id_card_image else None,
                    "status": boy.status
                }, status=status.HTTP_200_OK)
            except DeliveryAgent.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DeliveryBoyProfileView(APIView):
    def get(self, request):
        agent_id = request.query_params.get('agent_id')
        if not agent_id:
            return Response({"error": "Agent ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            agent = DeliveryAgent.objects.get(id=agent_id)
            serializer = DeliveryBoySerializer(agent)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DeliveryAgent.DoesNotExist:
            return Response({"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND)
        
        
class ConfirmDeliveryView(APIView):
    """Confirm order delivery via QR code scan"""

    def patch(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {"status": "error", "message": "Order ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Get order
        order = get_object_or_404(Order, id=order_id)

        # ✅ Prevent multiple deliveries
        if order.status == "order delivered":
            return Response(
                {"status": "error", "message": "This order has already been delivered."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Update order status
        order.status = "order delivered"
        order.save()

        # ✅ Send delivery confirmation email
        subject = f"🎉 Order #{order.id} Delivered Successfully!"
        context = {
            "user": order.user,
            "order": order,
        }
        html_content = render_to_string("order_delivered.html", context)
        text_content = f"Hi {order.user.username}, your order #{order.id} has been delivered successfully!"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        return Response(
            {"status": "success", "message": "Order marked as delivered and email sent."},
            status=status.HTTP_200_OK
        )
        

# class AssignedOnTheWayOrdersView(APIView):

#     def get(self, request):
#         agent_id = request.query_params.get('agent_id')

#         if not agent_id:
#             return Response({"error": "agent_id is required as a query parameter."},
#                             status=status.HTTP_400_BAD_REQUEST)

#         try:
#             agent = DeliveryAgent.objects.get(id=agent_id)
#         except DeliveryAgent.DoesNotExist:
#             return Response({"error": "Delivery agent not found."},
#                             status=status.HTTP_404_NOT_FOUND)

#         # ✅ Fetch only assigned orders where status is "order on the way"
#         assigned_orders = Order.objects.filter(
#             assigned_agent=agent,
#             status="order on the way"
#         )

#         if not assigned_orders.exists():
#             return Response({"message": "No 'order on the way' orders assigned."},
#                             status=status.HTTP_200_OK)

#         serializer = OrderSerializer(assigned_orders, many=True)
#         return Response({"assigned_orders": serializer.data}, status=status.HTTP_200_OK)

class AssignedOnTheWayOrdersView(APIView):

    def get(self, request):
        agent_id = request.query_params.get('agent_id')

        if not agent_id:
            return Response(
                {"error": "agent_id is required as a query parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = DeliveryAgent.objects.get(id=agent_id)
        except DeliveryAgent.DoesNotExist:
            return Response(
                {"error": "Delivery agent not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------------------------------------------
        # Fetch "order on the way" orders
        # ---------------------------------------------
        on_the_way_orders = Order.objects.filter(
            assigned_agent=agent,
            status="order on the way"
        )

        # ---------------------------------------------
        # Fetch "order delivered" orders
        # ---------------------------------------------
        delivered_orders = Order.objects.filter(
            assigned_agent=agent,
            status="order delivered"
        )

        # Serialize both sets
        on_the_way_serializer = OrderSerializer(on_the_way_orders, many=True)
        delivered_serializer = OrderSerializer(delivered_orders, many=True)

        return Response({
            "on_the_way_orders": on_the_way_serializer.data,
            "delivered_orders": delivered_serializer.data
        }, status=status.HTTP_200_OK)



    
class OrderDetailView(APIView):

    def get(self, request):
        order_id = request.query_params.get('order_id')

        if not order_id:
            return Response({"error": "order_id is required as a query parameter."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response({"order_details": serializer.data}, status=status.HTTP_200_OK)
    

class UpdateDeliveryAgentProfileView(generics.UpdateAPIView):
    queryset =DeliveryAgent.objects.all()
    serializer_class = DeliveryBoySerializer
    http_method_names = ["patch"]
    
    def update(self, request, *args, **kwargs):
        delivery_agent_id = request.data.get('delivery_agent_id')
        if not delivery_agent_id:
            return Response(
                {"details": "Delivery Agent ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = DeliveryAgent.objects.get(id = delivery_agent_id)
        
        except DeliveryAgent.DoesNotExist:
            return Response(
                {"details": "Delivery Agent not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(agent,data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(
            {"details": "Profile updated successfully"},
            status=status.HTTP_200_OK
        )
        
class UpdateDeliveryAgentLocationView(APIView):
    """
    API for delivery agents to update their current location
    PATCH: /delivery/update-location/
    """
    
    def patch(self, request):
        agent_id = request.data.get('agent_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        is_available = request.data.get('is_available')  # Optional
        
        if not agent_id:
            return Response({
                "status": "error",
                "message": "agent_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not latitude or not longitude:
            return Response({
                "status": "error",
                "message": "latitude and longitude are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            agent = DeliveryAgent.objects.get(id=agent_id, status='approved')
            
            # Update location
            agent.latitude = latitude
            agent.longitude = longitude
            
            # Update availability if provided
            if is_available is not None:
                agent.is_available = is_available
                
            agent.save()
            
            return Response({
                "status": "success",
                "message": "Location updated successfully",
                "data": {
                    "agent_id": agent.id,
                    "username": agent.username,
                    "latitude": float(agent.latitude),
                    "longitude": float(agent.longitude),
                    "is_available": agent.is_available
                }
            }, status=status.HTTP_200_OK)
            
        except DeliveryAgent.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Delivery agent not found or not approved"
            }, status=status.HTTP_404_NOT_FOUND)
        
class GetAvailableDeliveryAgentsView(APIView):
    """
    API to get available delivery agents near a location
    GET: /delivery/available-agents/?latitude=xx&longitude=xx&radius=10
    Returns agents within specified radius sorted by distance
    """
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get(self, request):
        # Get query parameters
        user_lat = request.query_params.get('latitude')
        user_lon = request.query_params.get('longitude')
        search_radius = request.query_params.get('radius', 10)  # Default 10km
        place = request.query_params.get('place')  # Optional: filter by place (district)
        order_id = request.query_params.get('order_id')  # Optional: to exclude already assigned agent
        
        # Validate required parameters
        if not user_lat or not user_lon:
            return Response({
                "status": "error",
                "message": "latitude and longitude are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
            search_radius = float(search_radius)
        except ValueError:
            return Response({
                "status": "error",
                "message": "Invalid latitude, longitude, or radius values"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all approved and available agents
        agents = DeliveryAgent.objects.filter(
            status='approved',
            is_available=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Filter by place if provided
        place = request.query_params.get('place')
        if place:
            agents = agents.filter(place=place)
            print(f"DEBUG - Filtering by place: {place}, found: {agents.count()} agents")
        
        # Filter by place if provided
        place = request.query_params.get('place')
        if place:
            agents = agents.filter(place=place)
        
        # If order_id provided, exclude the currently assigned agent (if any)
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.assigned_agent:
                    agents = agents.exclude(id=order.assigned_agent.id)
            except Order.DoesNotExist:
                pass
        
        # Calculate distances and filter within radius
        nearby_agents = []
        print(f"DEBUG - Processing {agents.count()} agents for distance calculation")
        
        for agent in agents:
            try:
                print(f"DEBUG - Agent {agent.id}: lat={agent.latitude}, lon={agent.longitude}")
                
                distance = self.calculate_distance(
                    user_lat, user_lon,
                    float(agent.latitude), float(agent.longitude)
                )
                print(f"DEBUG - Agent {agent.id}: distance={distance}km")
                
                # Check if within search radius AND within agent's service radius
                if distance <= search_radius and distance <= agent.service_radius:
                    print(f"DEBUG - Agent {agent.id} is within range")
                    
                    # Handle profile image safely
                    profile_image_url = None
                    if agent.profile_image:
                        try:
                            profile_image_url = agent.profile_image.url
                        except:
                            profile_image_url = None
                    
                    nearby_agents.append({
                        "id": agent.id,
                        "username": agent.username,
                        "phone": agent.phone,
                        "email": agent.email,
                        "place": agent.place,
                        "place_display": dict(DISTRICT_CHOICES).get(agent.place, agent.place) if hasattr(agent, 'place') else None,
                        "profile_image": profile_image_url,
                        "latitude": float(agent.latitude),
                        "longitude": float(agent.longitude),
                        "distance_km": round(distance, 2),
                        "service_radius": agent.service_radius,
                        "is_available": agent.is_available
                    })
                else:
                    print(f"DEBUG - Agent {agent.id} outside range (distance={distance} > radius={search_radius} or > service_radius={agent.service_radius})")
                    
            except Exception as e:
                print(f"DEBUG - Error processing agent {agent.id}: {str(e)}")
                continue
        
        print(f"DEBUG - Found {len(nearby_agents)} nearby agents")
        
        # Sort by distance (closest first)
        nearby_agents.sort(key=lambda x: x["distance_km"])
        
        # Sort by distance (closest first)
        nearby_agents.sort(key=lambda x: x["distance_km"])
        
        return Response({
            "status": "success",
            "count": len(nearby_agents),
            "agents": nearby_agents
        }, status=status.HTTP_200_OK)