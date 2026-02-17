from django.shortcuts import render,redirect
from .models import Doctor, TimeSlot, DoctorFeedback, DoctorComplaint, Prescription
from userapp.models import Appointment, Feedback, Complaint, Pet
from .serializers import *
from rest_framework.response import Response
from rest_framework import status,viewsets,generics
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta, time, date
# Create your views here.

# class DoctorRegistrationView(viewsets.ModelViewSet):
#     queryset = Doctor.objects.all()
#     serializer_class = DoctorSerializer
#     http_method_names = ['post']  # only POST allowed

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             self.perform_create(serializer)
#             return Response({
#                 "status": "success",
#                 "message": "Doctor Registered Successfully",
#                 "data": serializer.data
#             }, status=status.HTTP_201_CREATED)
#         else:
#             return Response({
#                 "status": "failed",
#                 "message": "Invalid Details",
#                 "errors": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

class DoctorRegistrationView(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    http_method_names = ['post']  # only POST allowed

    def create(self, request, *args, **kwargs):

        # ✅ Check duplicate email
        email = request.data.get("email")
        if email and Doctor.objects.filter(email=email).exists():
            return Response({
                "status": "failed",
                "message": "Email already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

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
    
    
# class TodayBookingsAPIView(APIView):
#     """
#     GET /doctor/today-bookings/?doctor_id=<id>
#     Returns today's appointments for the specified doctor.
#     """

#     def get(self, request):
#         doctor_id = request.query_params.get('doctor_id')

#         # ✅ 1. Validate doctor_id
#         if not doctor_id:
#             return Response({"error": "doctor_id query parameter is required."},
#                             status=status.HTTP_400_BAD_REQUEST)

#         # ✅ 2. Check doctor exists
#         try:
#             doctor = Doctor.objects.get(id=doctor_id)
#         except Doctor.DoesNotExist:
#             return Response({"error": "Doctor not found."},
#                             status=status.HTTP_404_NOT_FOUND)

#         # ✅ 3. Get today's date
#         today = date.today()

#         # ✅ 4. Fetch all appointments for today
#         appointments = Appointment.objects.filter(doctor=doctor, date=today).select_related('pet', 'slot')

#         # ✅ 5. Format response data
#         data = []
#         for appointment in appointments:
#             data.append({
#                 "appointment_id": appointment.id,
#                 "pet": {
#                     "id": appointment.pet.id,
#                     "name": appointment.pet.name,
#                     "category": appointment.pet.category.petcategory,
#                     "sub_category": appointment.pet.sub_category.petsubcategory,
#                     "gender": appointment.pet.gender,
#                     "weight": appointment.pet.weight,
#                 },
#                 "date": str(appointment.date),
#                 "slot": f"{appointment.slot.start_time.strftime('%H:%M')} - {appointment.slot.end_time.strftime('%H:%M')}" if appointment.slot else None,
#                 "reason": appointment.reason,
#                 "symptoms": appointment.symptoms if appointment.reason != "Vaccine" else None,
#                 "booking_option": "Clinical appointment"
#             })

#         return Response({
#             "doctor_name": doctor.full_name,
#             "total_bookings": len(data),
#             "bookings": data
#         }, status=status.HTTP_200_OK)

# class TodayBookingsAPIView(APIView):
#     """
#     GET /doctor/today-bookings/?doctor_id=<id>
#     Returns today's appointments for the specified doctor.
#     """

#     def get(self, request):
#         doctor_id = request.query_params.get('doctor_id')

#         # Validate doctor_id
#         if not doctor_id:
#             return Response({"error": "doctor_id query parameter is required."},
#                             status=status.HTTP_400_BAD_REQUEST)

#         # Check doctor exists
#         try:
#             doctor = Doctor.objects.get(id=doctor_id)
#         except Doctor.DoesNotExist:
#             return Response({"error": "Doctor not found."},
#                             status=status.HTTP_404_NOT_FOUND)

#         today = date.today()

#         appointments = Appointment.objects.filter(
#             doctor=doctor, 
#             date=today
#         ).select_related('pet', 'slot')

#         data = []
#         for appointment in appointments:

#             # Slot format
#             slot_time = (
#                 f"{appointment.slot.start_time.strftime('%H:%M')} - "
#                 f"{appointment.slot.end_time.strftime('%H:%M')}"
#                 if appointment.slot else None
#             )

#             # Booking type readable text
#             booking_type = (
#                 "Clinical Appointment"
#                 if appointment.appointment_type == "clinical"
#                 else "Audio Call Appointment"
#             )

#             data.append({
#                 "appointment_id": appointment.id,
#                 "appointment_type": appointment.appointment_type,
#                 # "booking_type": booking_type,

#                 "pet": {
#                     "id": appointment.pet.id,
#                     "name": appointment.pet.name,
#                     "category": appointment.pet.category.petcategory,
#                     "sub_category": appointment.pet.sub_category.petsubcategory,
#                     "gender": appointment.pet.gender,
#                     "weight": appointment.pet.weight,
#                 },

#                 "date": str(appointment.date),

#                 # 🔥 Slot details
#                 "slot_id": appointment.slot.id if appointment.slot else None,
#                 "slot": slot_time,

#                 # Reason only for clinical
#                 "reason": appointment.reason if appointment.appointment_type == "clinical" else None,

#                 # Symptoms allowed for both
#                 "symptoms": appointment.symptoms,

#                 # "notes": appointment.notes,
#             })

#         return Response({
#             "doctor_name": doctor.full_name,
#             "total_bookings": len(data),
#             "bookings": data
#         }, status=status.HTTP_200_OK)

class TodayBookingsAPIView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')

        if not doctor_id:
            return Response({"error": "doctor_id query parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found."},
                            status=status.HTTP_404_NOT_FOUND)

        today = date.today()

        # EXCLUDE completed and cancelled appointments
        appointments = Appointment.objects.filter(
            doctor=doctor,
            date=today,
            diagnosis_and_verdict__isnull=True
        ).exclude(
            status__in=['completed', 'cancelled']
        ).select_related('pet', 'slot')

        data = []
        for appointment in appointments:

            slot_time = (
                f"{appointment.slot.start_time.strftime('%H:%M')} - "
                f"{appointment.slot.end_time.strftime('%H:%M')}"
                if appointment.slot else None
            )

            data.append({
                "appointment_id": appointment.id,
                "appointment_type": appointment.appointment_type,

                "pet": {
                    "id": appointment.pet.id,
                    "name": appointment.pet.name,
                    "category": appointment.pet.category.petcategory,
                    "sub_category": appointment.pet.sub_category.petsubcategory,
                    "gender": appointment.pet.gender,
                    "weight": appointment.pet.weight,
                },

                "date": str(appointment.date),

                "slot_id": appointment.slot.id if appointment.slot else None,
                "slot": slot_time,

                "reason": appointment.reason if appointment.appointment_type == "clinical" else None,
                "symptoms": appointment.symptoms,
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
        
        
class CompleteAppointmentAPIView(APIView):
    """
    PATCH - Complete a clinical appointment and create prescription
    Input:
        - booking_id (Appointment ID)
        - weight
        - diagnosis_and_verdict
        - medication_name (required)
        - dosage (required)
        - food_timing (before/after)
        - time_of_day (list, e.g., ["morning", "night"])
        - days_duration
        - notes (optional)
    Output:
        - success message with prescription details
    """

    def patch(self, request):
        booking_id = request.data.get('booking_id')
        if not booking_id:
            return Response(
                {"error": "booking_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = get_object_or_404(Appointment, id=booking_id)
        
        # Check if prescription already exists
        if Prescription.objects.filter(appointment=appointment).exists():
            return Response(
                {"error": "Prescription already exists for this appointment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate prescription required fields - medications list
        medications = request.data.get('medications')
        
        if not medications or not isinstance(medications, list) or len(medications) == 0:
            return Response(
                {"error": "medications list is required and must contain at least one medication"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate each medication has required fields
        for idx, med in enumerate(medications):
            if not med.get('name'):
                return Response(
                    {"error": f"Medication #{idx+1}: name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not med.get('dosage'):
                return Response(
                    {"error": f"Medication #{idx+1}: dosage is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if med.get('food_timing') and med['food_timing'] not in ['before', 'after']:
                return Response(
                    {"error": f"Medication #{idx+1}: food_timing must be 'before' or 'after'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if med.get('time_of_day'):
                if not isinstance(med.get('time_of_day'), list):
                    return Response(
                        {"error": f"Medication #{idx+1}: time_of_day must be a list"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Validate each time value is from allowed choices
                from .constants import VALID_TIME_OF_DAY_VALUES
                for time_val in med.get('time_of_day'):
                    if time_val not in VALID_TIME_OF_DAY_VALUES:
                        return Response(
                            {"error": f"Medication #{idx+1}: '{time_val}' is not a valid time. Allowed values: {', '.join(VALID_TIME_OF_DAY_VALUES)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

        # Update appointment
        serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # Update pet's weight if provided
            weight = serializer.validated_data.get('weight')
            if weight is not None:
                pet = appointment.pet
                pet.weight = weight
                pet.save(update_fields=['weight'])

            # Create prescription with multiple medications
            prescription = Prescription.objects.create(
                appointment=appointment,
                doctor=appointment.doctor,
                pet=appointment.pet,
                medications=request.data.get('medications', []),
                days_duration=request.data.get('days_duration', 7),
                notes=request.data.get('notes', '')
            )

            # Change appointment status to 'completed'
            appointment.status = 'completed'
            appointment.save(update_fields=['status'])

            # Serialize prescription for response
            from .serializers import PrescriptionSerializer
            prescription_serializer = PrescriptionSerializer(prescription)

            return Response(
                {
                    "success": True, 
                    "message": "Appointment completed and prescription created successfully.",
                    "prescription": prescription_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class TreatmentHistoryAPIView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        date = request.query_params.get('date')

        if not doctor_id or not date:
            return Response(
                {"error": "Both doctor_id and date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Get only completed treatments
        appointments = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            diagnosis_and_verdict__isnull=False
        ).exclude(
            diagnosis_and_verdict__exact=''
        )

        serializer = TreatmentHistorySerializer(appointments, many=True)

        return Response({
            "success": True,
            "doctor_id": doctor_id,
            "date": date,
            "treatments": serializer.data
        }, status=status.HTTP_200_OK)

        
class TreatmentDetailAPIView(APIView):
    """
    GET - Fetch treatment details for a given appointment (booking)
    Input:
        booking_id (required)
    Output:
        Full treatment, doctor, and pet details (image paths start with media/)
    """

    def get(self, request):
        booking_id = request.query_params.get('booking_id')

        if not booking_id:
            return Response(
                {"error": "booking_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = get_object_or_404(Appointment, id=booking_id)
        doctor = appointment.doctor
        pet = appointment.pet

        # Get relative image paths (media/...)
        pet_image = pet.pet_image.url if pet.pet_image else None
        doctor_image = doctor.image.url if doctor.image else None
        doctor_id_card = doctor.id_card.url if doctor.id_card else None

        treatment_data = {
            "booking_id": appointment.id,
            "appointment_type": appointment.appointment_type,
            "date": appointment.date,
            "slot": str(appointment.slot),
            "reason": appointment.reason,
            "symptoms": appointment.symptoms,
            "diagnosis": appointment.diagnosis_and_verdict,
            # "verdict": appointment.verdict,
            "notes": appointment.notes,

            "pet_details": {
                "id": pet.id,
                "name": pet.name,
                "owner_name": pet.user.username if pet.user else None,
                "birth_date": pet.birth_date.strftime("%Y-%m-%d") if pet.birth_date else None,
                "gender": pet.gender,
                "weight": pet.weight,
                "health_condition": getattr(pet, "health_condition", None),
                "category": pet.category.petcategory if pet.category else None,
                "sub_category": pet.sub_category.petsubcategory if pet.sub_category else None,
                "image": pet_image  # relative path: media/...
            },

            "doctor_details": {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "email": doctor.email,
                "phone_number": doctor.phone_number,
                "address": doctor.address,
                "latitude": float(doctor.latitude),
                "longitude": float(doctor.longitude),
                "status": doctor.status,
                "is_approved": doctor.is_approved,
                "image": doctor_image,  # relative path: media/...
                "id_card": doctor_id_card  # relative path: media/...
            }
        }

        return Response(
            {"success": True, "treatment_details": treatment_data},
            status=status.HTTP_200_OK
        )
        

class UpdateDoctorProfileView(generics.UpdateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):

        doctor_id = request.data.get('doctor_id')
        if not doctor_id:
            return Response(
                {"detail": "Doctor ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(doctor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "detail": "Doctor profile updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class DoctorFeedbackListView(APIView):

    def get(self, request):
        doctor_id = request.query_params.get("doctor_id")

        if not doctor_id:
            return Response({
                "status": "error",
                "message": "doctor_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        feedbacks = Feedback.objects.filter(appointment__doctor_id=doctor_id).order_by('-created_at')

        # Custom response data with user name
        feedback_data = []
        for feedback in feedbacks:
            # Get user name from pet owner
            user_name = None
            if feedback.appointment and feedback.appointment.pet and feedback.appointment.pet.user:
                user_name = feedback.appointment.pet.user.username
            elif hasattr(feedback, 'user_name') and feedback.user_name:
                # Fallback to stored user_name if available (for backward compatibility)
                user_name = feedback.user_name
            
            feedback_data.append({
                "id": feedback.id,
                "rating": feedback.rating,
                "feedback": feedback.feedback,
                "created_at": feedback.created_at.strftime("%Y-%m-%d %H:%M:%S") if feedback.created_at else None,
                "appointment": feedback.appointment.id if feedback.appointment else None,
                "user_name": user_name  # Add user name to response
            })
        
        return Response({
            "status": "success",
            "doctor_id": doctor_id,
            "count": feedbacks.count(),
            "data": feedback_data
        }, status=status.HTTP_200_OK)
        
        
class DoctorComplaintListView(APIView):

    def get(self, request):
        doctor_id = request.query_params.get("doctor_id")

        if not doctor_id:
            return Response({
                "status": "error",
                "message": "doctor_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter complaints where appointment doctor is this doctor
        complaints = Complaint.objects.filter(
            appointment__doctor_id=doctor_id
        ).order_by('-created_at')

        serializer = ComplaintSerializer(complaints, many=True)

        return Response({
            "status": "success",
            "doctor_id": doctor_id,
            "count": complaints.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    
class DoctorSlotManagementView(APIView):
    """
    API for doctors to manage their time slots
    GET: View all slots with current bookings
    PATCH: Update slot availability (cancel slot)
    """
    
    def get(self, request):
        """Get all slots for a doctor with booking information"""
        doctor_id = request.query_params.get('doctor_id')
        date = request.query_params.get('date')  # Optional: filter by specific date
        
        if not doctor_id:
            return Response({
                "status": "error",
                "message": "doctor_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Doctor not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all slots for this doctor
        slots = TimeSlot.objects.filter(doctor=doctor).order_by('start_time')
        
        # Import CancelledSlot model
        from .models import CancelledSlot
        
        slot_data = []
        for slot in slots:
            # Get appointments for this slot (filter by date if provided)
            appointments_query = Appointment.objects.filter(
                doctor=doctor,
                slot=slot
            ).exclude(status='cancelled')
            
            cancelled_dates_list = []
            if date:
                try:
                    appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
                    appointments_query = appointments_query.filter(date=appointment_date)
                    
                    # Check if this slot is cancelled for the specific date
                    is_cancelled_today = CancelledSlot.objects.filter(
                        doctor=doctor,
                        slot=slot,
                        date=appointment_date
                    ).exists()
                    
                    if is_cancelled_today:
                        cancelled_dates_list.append(str(appointment_date))
                        
                except ValueError:
                    return Response({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD."
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Get all cancelled dates for this slot
                cancelled_records = CancelledSlot.objects.filter(
                    doctor=doctor,
                    slot=slot
                ).values_list('date', flat=True)
                cancelled_dates_list = [str(d) for d in cancelled_records]
            
            appointments = appointments_query.select_related('pet', 'pet__user')
            booked_count = appointments.count()
            
            slot_data.append({
                "slot_id": slot.id,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "is_available": slot.is_available,
                "booked_count": booked_count,
                "cancelled_dates": cancelled_dates_list,
                "is_cancelled_for_date": len(cancelled_dates_list) > 0 if date else False,
                "appointments": [
                    {
                        "appointment_id": app.id,
                        "pet_name": app.pet.name,
                        "user_name": app.pet.user.username if app.pet and app.pet.user else None,
                        "user_email": app.pet.user.email if app.pet and app.pet.user else None,
                        "appointment_type": app.appointment_type,
                        "status": app.status,
                        "date": str(app.date)
                    }
                    for app in appointments
                ]
            })
        
        return Response({
            "status": "success",
            "doctor_id": doctor_id,
            "doctor_name": doctor.full_name,
            "date_filter": date,
            "total_slots": len(slot_data),
            "slots": slot_data
        }, status=status.HTTP_200_OK)
    
        
    def patch(self, request):
        """Doctor cancels slots for specific dates - creates CancelledSlot records and cancels existing appointments"""
        doctor_id = request.data.get('doctor_id')
        slot_ids = request.data.get('slot_ids')  # Array of slot IDs
        slot_id = request.data.get('slot_id')  # Backward compatibility for single slot
        date = request.data.get('date')  # Required: specific date for cancellation
        cancel_reason = request.data.get('reason', 'Doctor unavailable')
        
        # Validate date is required
        if not date:
            return Response({
                "status": "error",
                "message": "date is required for slot cancellation (YYYY-MM-DD)."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse date
        try:
            cancellation_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "status": "error",
                "message": "Invalid date format. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle both single slot_id and multiple slot_ids
        if slot_ids:
            if not isinstance(slot_ids, list):
                return Response({
                    "status": "error",
                    "message": "slot_ids must be an array/list."
                }, status=status.HTTP_400_BAD_REQUEST)
            slots_to_cancel = slot_ids
        elif slot_id:
            slots_to_cancel = [slot_id]
        else:
            return Response({
                "status": "error",
                "message": "Either slot_id or slot_ids is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not doctor_id:
            return Response({
                "status": "error",
                "message": "doctor_id is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Doctor not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Import CancelledSlot model
        from .models import CancelledSlot
        
        # Initialize results tracking
        cancelled_slots = []
        total_appointments_cancelled = 0
        slot_errors = []
        
        # Process each slot
        for current_slot_id in slots_to_cancel:
            try:
                slot = TimeSlot.objects.get(id=current_slot_id, doctor=doctor)
                
                # Create CancelledSlot record (unique_together prevents duplicates)
                cancelled_slot_record, created = CancelledSlot.objects.get_or_create(
                    doctor=doctor,
                    slot=slot,
                    date=cancellation_date,
                    defaults={'reason': cancel_reason}
                )
                
                if not created:
                    # Update existing record's reason if needed
                    cancelled_slot_record.reason = cancel_reason
                    cancelled_slot_record.save()
                
                # DO NOT modify slot.is_available - keep it as True for future dates
                
                # Find appointments to cancel for this slot on this specific date
                appointments_query = Appointment.objects.filter(
                    doctor=doctor,
                    slot=slot,
                    date=cancellation_date,
                    status__in=['booked', 'payment_completed']  # Only cancel active appointments
                )
                
                appointments = appointments_query.select_related('pet', 'pet__user')
                slot_cancelled_count = 0
                
                # Cancel each appointment for this slot on this date
                for appointment in appointments:
                    appointment.status = 'cancelled'
                    appointment.notes = f"Doctor cancelled for {cancellation_date}: {cancel_reason}"
                    appointment.save()
                    slot_cancelled_count += 1
                    
                    # Send email notification to user
                    if appointment.pet and appointment.pet.user and appointment.pet.user.email:
                        try:
                            self.send_cancellation_email(appointment, cancel_reason, cancellation_date)
                        except Exception as e:
                            # Log error but don't fail the cancellation process
                            print(f"Email sending failed for appointment {appointment.id}: {str(e)}")
                
                # Track successful slot cancellation
                cancelled_slots.append({
                    "slot_id": current_slot_id,
                    "slot_time": f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}",
                    "date": str(cancellation_date),
                    "appointments_cancelled": slot_cancelled_count,
                    "cancellation_record_created": created
                })
                total_appointments_cancelled += slot_cancelled_count
                
            except TimeSlot.DoesNotExist:
                slot_errors.append({
                    "slot_id": current_slot_id,
                    "error": "Slot not found or does not belong to this doctor."
                })
            except Exception as e:
                slot_errors.append({
                    "slot_id": current_slot_id,
                    "error": str(e)
                })
        
        # Prepare response
        response_data = {
            "status": "success",
            "message": f"Cancelled {len(cancelled_slots)} slot(s) for {date}. {total_appointments_cancelled} appointment(s) cancelled.",
            "cancelled_slots": cancelled_slots,
            "total_appointments_cancelled": total_appointments_cancelled,
            "cancellation_reason": cancel_reason,
            "cancellation_date": date
        }
        
        # Add errors if any
        if slot_errors:
            response_data["slot_errors"] = slot_errors
            response_data["partial_success"] = True
        
        return Response(response_data, status=status.HTTP_200_OK)
    
        
    def send_cancellation_email(self, appointment, cancel_reason, cancellation_date=None):
        """Send email notification to user when doctor cancels appointment"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        
        user = appointment.pet.user
        doctor = appointment.doctor
        
        subject = f"⚠️ Appointment Cancelled: Your {appointment.appointment_type} appointment with Dr. {doctor.full_name}"
        
        context = {
            "user": user,
            "appointment": appointment,
            "doctor": doctor,
            "cancel_reason": cancel_reason,
            "cancellation_date": cancellation_date or appointment.date,
            "slot_time": f"{appointment.slot.start_time.strftime('%H:%M')} - {appointment.slot.end_time.strftime('%H:%M')}"
        }
        
        try:
            # Render HTML email
            html_content = render_to_string("doctor_slot_cancelled.html", context)
            text_content = f"""
            Dear {user.username},
            
            Your appointment with Dr. {doctor.full_name} has been cancelled by the doctor.
            
            Appointment Details:
            - Date: {appointment.date}
            - Time: {appointment.slot.start_time.strftime('%H:%M')} - {appointment.slot.end_time.strftime('%H:%M')}
            - Pet: {appointment.pet.name}
            - Type: {appointment.appointment_type}
            - Reason for cancellation: {cancel_reason}
            
            Please book another slot at your convenience.
            
            Best regards,
            Pet Cure Team
            """
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)  # Fail silently to not interrupt the cancellation process
            
        except Exception as e:
            # Log error but don't fail the whole cancellation process
            print(f"Failed to send cancellation email for appointment {appointment.id}: {str(e)}")


class DoctorAvailableSlotsView(APIView):
    """
    API for doctors to get available time slots for a specific date
    GET: Returns all available slots for the given date
    """
    
    def get(self, request):
        """Get available slots for a doctor on a specific date"""
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')
        
        if not doctor_id or not date_str:
            return Response({
                "status": "error",
                "message": "doctor_id and date are required as query parameters."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Doctor not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "status": "error",
                "message": "Invalid date format. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if date is in past
        if target_date < date.today():
            return Response({
                "status": "error",
                "message": "Cannot view slots for past dates."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current time in local timezone
        from django.utils import timezone
        import pytz
        
        # Get current time in UTC
        now_utc = timezone.now()
        
        # Convert to Asia/Kolkata timezone
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        now_kolkata = now_utc.astimezone(kolkata_tz)
        current_time = now_kolkata.time()
        today_date = now_kolkata.date()
        
        # Get all slots for this doctor
        slots = TimeSlot.objects.filter(doctor=doctor).order_by('start_time')
        
        # Import CancelledSlot model
        from .models import CancelledSlot
        
        slot_data = []
        for slot in slots:
            # Skip slots that have already passed for today
            if target_date == today_date:
                if slot.start_time <= current_time:
                    continue  # Skip past slots for today
            
            # Check if this slot is cancelled by doctor for this specific date
            is_cancelled_by_doctor = CancelledSlot.objects.filter(
                doctor=doctor,
                slot=slot,
                date=target_date
            ).exists()
            
            print(f"DEBUG - Slot {slot.id}: cancelled_by_doctor = {is_cancelled_by_doctor}")
            
            # Count non-cancelled appointments for this slot on this date
            booked_count = Appointment.objects.filter(
                doctor=doctor,
                slot=slot,
                date=target_date
            ).exclude(status='cancelled').count()
            
            print(f"DEBUG - Slot {slot.id}: booked_count = {booked_count}")
            
            # Check if slot is available (NOT cancelled by doctor AND NOT fully booked)
            if is_cancelled_by_doctor:
                is_available = False
                remarks = "Unavailable (Doctor cancelled this slot for this date)"
            else:
                is_available = booked_count < 4
                remarks = "Fully Booked" if not is_available else f"{4 - booked_count} seats available"
            
            slot_data.append({
                "slot_id": slot.id,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "availability": is_available,
                "booked_count": booked_count,
                "available_seats": max(0, 4 - booked_count) if is_available else 0,
                "remarks": remarks,
                "cancelled_by_doctor": is_cancelled_by_doctor
            })
        
        return Response({
            "status": "success",
            "doctor_id": doctor_id,
            "doctor_name": doctor.full_name,
            "date": date_str,
            "total_slots": len(slot_data),
            "available_slots": len([s for s in slot_data if s['availability']]),
            "slots": slot_data
        }, status=status.HTTP_200_OK)
    


class PrescriptionAPIView(APIView):
    """
    API for viewing prescriptions
    GET: View prescriptions for appointments
    POST: Removed - Prescription creation is now handled in CompleteAppointmentAPIView
    """
    
    def get(self, request):
        """Get prescriptions for a doctor or specific appointment"""
        doctor_id = request.query_params.get('doctor_id')
        appointment_id = request.query_params.get('appointment_id')
        
        if not doctor_id:
            return Response({
                "status": "error",
                "message": "doctor_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Doctor not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Start with all prescriptions for this doctor
        prescriptions = Prescription.objects.filter(doctor=doctor)
        
        # Filter by appointment if provided
        if appointment_id:
            prescriptions = prescriptions.filter(appointment_id=appointment_id)
        
        # Order by latest first
        prescriptions = prescriptions.order_by('-issued_date')
        
        serializer = PrescriptionSerializer(prescriptions, many=True)
        
        return Response({
            "status": "success",
            "doctor_id": doctor_id,
            "count": prescriptions.count(),
            "prescriptions": serializer.data
        }, status=status.HTTP_200_OK)
    
class PrescriptionDetailView(APIView):
    """
    API for doctors to view a specific prescription by ID
    GET: /doctor/prescription-view/?prescription_id=<id>&doctor_id=<id>
    Returns detailed prescription information
    """
    
    def get(self, request):
        """Get detailed prescription by ID"""
        prescription_id = request.query_params.get('prescription_id')
        doctor_id = request.query_params.get('doctor_id')
        
        # Validate required parameters
        if not prescription_id:
            return Response({
                "status": "error",
                "message": "prescription_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not doctor_id:
            return Response({
                "status": "error",
                "message": "doctor_id is required as a query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify doctor exists
            doctor = Doctor.objects.get(id=doctor_id)
            
            # Get prescription and verify it belongs to this doctor
            prescription = Prescription.objects.get(
                id=prescription_id,
                doctor=doctor
            )
            
        except Doctor.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Doctor not found."
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Prescription.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Prescription not found or does not belong to this doctor."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize prescription data
        serializer = PrescriptionSerializer(prescription)
        
        # Get additional appointment and pet details
        appointment = prescription.appointment
        pet = prescription.pet
        
        # Build detailed response
        response_data = serializer.data
        response_data.update({
            "appointment_details": {
                "date": appointment.date,
                "slot": f"{appointment.slot.start_time.strftime('%H:%M')} - {appointment.slot.end_time.strftime('%H:%M')}" if appointment.slot else None,
                "type": appointment.appointment_type,
                "reason": appointment.reason,
                "symptoms": appointment.symptoms,
                "status": appointment.status
            },
            "pet_details": {
                "id": pet.id,
                "name": pet.name,
                "category": pet.category.petcategory if pet.category else None,
                "sub_category": pet.sub_category.petsubcategory if pet.sub_category else None,
                "gender": pet.gender,
                "age": pet.get_age(),
                "weight": pet.weight,
                "image": pet.pet_image.url if pet.pet_image else None
            },
            "doctor_details": {
                "id": doctor.id,
                "name": doctor.full_name,
                "email": doctor.email,
                "phone": doctor.phone_number
            }
        })
        
        return Response({
            "status": "success",
            "message": "Prescription details fetched successfully.",
            "prescription": response_data
        }, status=status.HTTP_200_OK)