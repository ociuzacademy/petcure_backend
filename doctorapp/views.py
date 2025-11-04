from django.shortcuts import render,redirect
from .models import *
from userapp.models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status,viewsets,generics
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

# Create your views here.

class DoctorRegistrationView(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    http_method_names = ['post']  # only POST allowed

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "message": "Doctor Registered Successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "failed",
                "message": "Invalid Details",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
            
class DoctorLoginAPIView(APIView):
    def post(self, request):
        serializer = DoctorLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                doctor = Doctor.objects.get(email=email, password=password)
            except Doctor.DoesNotExist:
                return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

            if doctor.status != 'approved':
                return Response({"error": "Your account is not approved yet"}, status=status.HTTP_403_FORBIDDEN)

            # Successful login
            data = {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "email": doctor.email,
                "phone_number": doctor.phone_number,
                "address": doctor.address,
                "image": f"media/{doctor.image.name}" if doctor.image else None,
                "id_card": f"media/{doctor.id_card.name}" if doctor.id_card else None,
            }

            return Response({"message": "Login successful", "doctor": data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class DoctorProfileView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')

        if not doctor_id:
            return Response({"error": "doctor_id is required as a query parameter."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = Doctor.objects.get(id=doctor_id, status='approved')
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found or not approved."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorSerializer(doctor)
        return Response({"doctor_profile": serializer.data}, status=status.HTTP_200_OK) 
    
    
class TodayBookingsAPIView(APIView):
    """
    GET /doctor/today-bookings/?doctor_id=<id>
    Returns today's appointments for the specified doctor.
    """

    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')

        # ✅ 1. Validate doctor_id
        if not doctor_id:
            return Response({"error": "doctor_id query parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ 2. Check doctor exists
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # ✅ 3. Get today's date
        today = date.today()

        # ✅ 4. Fetch all appointments for today
        appointments = Appointment.objects.filter(doctor=doctor, date=today).select_related('pet', 'slot')

        # ✅ 5. Format response data
        data = []
        for appointment in appointments:
            data.append({
                "appointment_id": appointment.id,
                "pet": {
                    "id": appointment.pet.id,
                    "name": appointment.pet.name,
                    "category": appointment.pet.category.petcategory,
                    "sub_category": appointment.pet.sub_category.petsubcategory,
                    "gender": appointment.pet.gender,
                    "weight": appointment.pet.weight,
                },
                "date": str(appointment.date),
                "slot": f"{appointment.slot.start_time.strftime('%H:%M')} - {appointment.slot.end_time.strftime('%H:%M')}" if appointment.slot else None,
                "reason": appointment.reason,
                "symptoms": appointment.symptoms if appointment.reason != "Vaccine" else None,
                "booking_option": "Clinical appointment"
            })

        return Response({
            "doctor_name": doctor.full_name,
            "total_bookings": len(data),
            "bookings": data
        }, status=status.HTTP_200_OK)
        
        
class BookingDetailsAPIView(APIView):
    def get(self, request):
        booking_id = request.query_params.get('booking_id')
        if not booking_id:
            return Response(
                {"success": False, "message": "Booking ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking = get_object_or_404(Appointment, id=booking_id)
        serializer = AppointmentSerializer(booking)

        return Response({
            "success": True,
            "message": "Booking details fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
        
