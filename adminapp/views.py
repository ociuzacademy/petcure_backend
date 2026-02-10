from django.shortcuts import render,redirect
from django.contrib import messages
from .models import *
from deliveryapp.models import *
from userapp.models import *
from django.template.defaulttags import register
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator

@register.filter
def get_item(dictionary, key):
    """Template filter to get dictionary item by key"""
    if dictionary and key:
        return dictionary.get(str(key))
    return None

def admin_index(request):
    return render(request,'admin_index.html')


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            admin = Admin.objects.get(email=email,password=password)
            request.session['admin_id'] = admin.id
            return redirect('admin_index')
        except Admin.DoesNotExist:
            return redirect('login')

    return render(request, 'login.html')

def logout(request):
    # Remove admin session if it exists
    if 'admin_id' in request.session:
        del request.session['admin_id']
    
    # Optionally clear all session data
    request.session.flush()
    
    # Redirect to login page
    return redirect('login')


def add_pet_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('petcategory')
        subcategories = request.POST.getlist('petsubcategory[]')

        if not category_name:
            messages.error(request, "Please enter a pet category name.")
            return redirect('add_pet_category')

        # Create or get category
        category, created = PetCategory.objects.get_or_create(petcategory=category_name.strip())

        # Add subcategories
        added = 0
        for sub in subcategories:
            sub = sub.strip()
            if sub:
                PetSubcategory.objects.get_or_create(petcategory=category, petsubcategory=sub)
                added += 1

        messages.success(request, f"Category '{category.petcategory}' saved with {added} subcategories.")
        return redirect('add_pet_category')

    # Show existing categories + subcategories
    categories = PetCategory.objects.prefetch_related('subcategories').all()
    return render(request, 'add_pet_category.html', {'categories': categories})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PetCategory, PetSubcategory

# Edit Category via POST (ID in form)
def edit_pet_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        new_name = request.POST.get('petcategory')
        category = get_object_or_404(PetCategory, id=category_id)
        if new_name:
            category.petcategory = new_name
            category.save()
            messages.success(request, "Category updated successfully!")
    return redirect('add_pet_category')


# Delete Category via POST (ID in form)
def delete_pet_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = get_object_or_404(PetCategory, id=category_id)
        category.delete()
        messages.success(request, "Category deleted successfully!")
    return redirect('add_pet_category')


# Edit Subcategory via POST (ID in form)
def edit_pet_subcategory(request):
    if request.method == 'POST':
        sub_id = request.POST.get('sub_id')
        new_name = request.POST.get('petsubcategory')
        sub = get_object_or_404(PetSubcategory, id=sub_id)
        if new_name:
            sub.petsubcategory = new_name
            sub.save()
            messages.success(request, "Subcategory updated successfully!")
    return redirect('add_pet_category')


# Delete Subcategory via POST (ID in form)
def delete_pet_subcategory(request):
    if request.method == 'POST':
        sub_id = request.POST.get('sub_id')
        sub = get_object_or_404(PetSubcategory, id=sub_id)
        sub.delete()
        messages.success(request, "Subcategory deleted successfully!")
    return redirect('add_pet_category')

def add_vaccine(request):
    if request.method == 'POST':
        subcategory_id = request.POST.get('subcategory')
        vaccine_name = request.POST.get('vaccine_name')
        recommended_age = request.POST.get('recommended_age')
        disease_protected = request.POST.get('disease_protected')
        booster_required = 'booster_required' in request.POST
        booster_timing = request.POST.get('booster_timing', '')
        annual_revaccination = 'annual_revaccination' in request.POST

        # Validate required fields
        if not all([subcategory_id, vaccine_name, recommended_age, disease_protected]):
            messages.error(request, "Please fill all required fields.")
            return redirect('add_vaccine')

        # Check for duplicate vaccine name in same subcategory
        try:
            subcategory = PetSubcategory.objects.get(id=subcategory_id)
            if Vaccine.objects.filter(subcategory=subcategory, vaccine_name__iexact=vaccine_name).exists():
                messages.error(request, f"Vaccine '{vaccine_name}' already exists for {subcategory.petsubcategory}.")
                return redirect('add_vaccine')
        except PetSubcategory.DoesNotExist:
            messages.error(request, "Invalid subcategory selected.")
            return redirect('add_vaccine')

        try:
            subcategory = PetSubcategory.objects.get(id=subcategory_id)
        except PetSubcategory.DoesNotExist:
            messages.error(request, "Invalid subcategory selected.")
            return redirect('add_vaccine')

        # Check if vaccine already exists for this subcategory
        if Vaccine.objects.filter(
            subcategory=subcategory, 
            vaccine_name__iexact=vaccine_name
        ).exists():
            messages.warning(request, f"Vaccine '{vaccine_name}' already exists for {subcategory.petsubcategory}.")
            return redirect('add_vaccine')

        # Create vaccine
        Vaccine.objects.create(
            subcategory=subcategory,
            vaccine_name=vaccine_name,
            recommended_age=recommended_age,
            disease_protected=disease_protected,
            booster_required=booster_required,
            booster_timing=booster_timing if booster_required else '',
            annual_revaccination=annual_revaccination
        )

        messages.success(request, f"Vaccine '{vaccine_name}' added successfully!")
        return redirect('add_vaccine')

    # GET request - show form
    subcategories = PetSubcategory.objects.all()
    return render(request, 'add_vaccine.html', {'subcategories': subcategories})

def edit_product_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        new_name = request.POST.get('productcategory')
        category = get_object_or_404(ProductCategory, id=category_id)
        if new_name:
            category.productcategory = new_name
            category.save()
            messages.success(request, "Product category updated successfully!")
        return redirect('add_product_category')

def edit_vaccine(request):
    if request.method == 'POST':
        vaccine_id = request.POST.get('vaccine_id')
        vaccine = get_object_or_404(Vaccine, id=vaccine_id)
        
        # Get updated data
        vaccine_name = request.POST.get('vaccine_name')
        recommended_age = request.POST.get('recommended_age')
        disease_protected = request.POST.get('disease_protected')
        booster_required = 'booster_required' in request.POST
        booster_timing = request.POST.get('booster_timing', '')
        annual_revaccination = 'annual_revaccination' in request.POST
        
        # Check for duplicate vaccine name (excluding current vaccine)
        if vaccine_name != vaccine.vaccine_name:
            if Vaccine.objects.filter(
                subcategory=vaccine.subcategory, 
                vaccine_name__iexact=vaccine_name
            ).exclude(id=vaccine_id).exists():
                messages.error(request, f"Vaccine '{vaccine_name}' already exists for {vaccine.subcategory.petsubcategory}.")
                return redirect('view_vaccines')
        
        # Update vaccine
        vaccine.vaccine_name = vaccine_name
        vaccine.recommended_age = recommended_age
        vaccine.disease_protected = disease_protected
        vaccine.booster_required = booster_required
        vaccine.booster_timing = booster_timing if booster_required else ''
        vaccine.annual_revaccination = annual_revaccination
        vaccine.save()
        
        messages.success(request, f"Vaccine '{vaccine_name}' updated successfully!")
        return redirect('view_vaccines')
    
    return redirect('view_vaccines')

# Delete Product Category
def delete_product_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = get_object_or_404(ProductCategory, id=category_id)
        category.delete()
        messages.success(request, "Product category deleted successfully!")
        return redirect('add_product_category')
    
def delete_vaccine(request):
    if request.method == 'POST':
        vaccine_id = request.POST.get('vaccine_id')
        vaccine = get_object_or_404(Vaccine, id=vaccine_id)
        vaccine_name = vaccine.vaccine_name
        vaccine.delete()
        messages.success(request, f"Vaccine '{vaccine_name}' deleted successfully!")
        return redirect('view_vaccines')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('view_vaccines')

def add_products(request):
    product_categories = ProductCategory.objects.all()
    pet_categories = PetCategory.objects.all()
    pet_subcategories = PetSubcategory.objects.all()  # All subcategories

    if request.method == "POST":
        productcategory = get_object_or_404(ProductCategory, id=request.POST.get("productcategory"))
        petcategory = get_object_or_404(PetCategory, id=request.POST.get("petcategory"))
        petsubcategory = get_object_or_404(PetSubcategory, id=request.POST.get("petsubcategory"))

        names = request.POST.getlist("name[]")
        descriptions = request.POST.getlist("description[]")
        prices = request.POST.getlist("price[]")
        stocks = request.POST.getlist("stock[]")

        for i in range(len(names)):
            product = Product.objects.create(
                productcategory=productcategory,
                petcategory=petcategory,
                petsubcategory=petsubcategory,
                name=names[i],
                description=descriptions[i] if i < len(descriptions) else "",
                price=prices[i] if i < len(prices) else 0,
                stock=stocks[i] if i < len(stocks) else 0
            )

            images = request.FILES.getlist(f"images_{i}")
            for img in images:
                ProductImage.objects.create(product=product, image=img)

        messages.success(request, f"{len(names)} product(s) added successfully!")
        return redirect("add_products")

    return render(request, "add_products.html", {
        "product_categories": product_categories,
        "pet_categories": pet_categories,
        "pet_subcategories": pet_subcategories
    })

def view_products(request):
    categories = ProductCategory.objects.all()
    selected_category = request.GET.get('category')

    if selected_category:
        products = Product.objects.filter(productcategory_id=selected_category).prefetch_related('images')
        try:
            selected_category_name = ProductCategory.objects.get(id=selected_category).productcategory
        except ProductCategory.DoesNotExist:
            selected_category_name = None
    else:
        products = Product.objects.all().prefetch_related('images')
        selected_category_name = None

    return render(request, 'view_products.html', {
        'categories': categories,
        'selected_category': selected_category,
        'selected_category_name': selected_category_name,
        'products': products,
    })
    
def view_vaccines(request):
    # Get filter parameters
    subcategory_id = request.GET.get('subcategory')
    petcategory_id = request.GET.get('petcategory')
    
    # Start with all vaccines
    vaccines = Vaccine.objects.select_related('subcategory__petcategory').all()
    
    # Apply filters if provided
    if subcategory_id:
        vaccines = vaccines.filter(subcategory_id=subcategory_id)
    
    if petcategory_id:
        vaccines = vaccines.filter(subcategory__petcategory_id=petcategory_id)
    
    # Get all categories and subcategories for filter dropdowns
    pet_categories = PetCategory.objects.all()
    pet_subcategories = PetSubcategory.objects.all()
    
    return render(request, 'view_vaccines.html', {
        'vaccines': vaccines,
        'pet_categories': pet_categories,
        'pet_subcategories': pet_subcategories,
        'selected_petcategory': int(petcategory_id) if petcategory_id else None,
        'selected_subcategory': int(subcategory_id) if subcategory_id else None,
    })

def edit_products(request):
    product_id = request.GET.get('id')
    product = get_object_or_404(Product, id=product_id)
    productcategories = ProductCategory.objects.all()
    petcategories = PetCategory.objects.all()
    petsubcategories = PetSubcategory.objects.all()

    if request.method == 'POST':
        product.productcategory_id = request.POST['productcategory']
        product.petcategory_id = request.POST['petcategory']
        product.petsubcategory_id = request.POST['petsubcategory']
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        product.save()

        # Remove selected images
        remove_images = request.POST.getlist('remove_images')
        if remove_images:
            ProductImage.objects.filter(id__in=remove_images).delete()

        # Add new images
        for img in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=img)

        return redirect('view_products')

    return render(request, 'edit products.html', {
        'product': product,
        'productcategories': productcategories,
        'petcategories': petcategories,
        'petsubcategories': petsubcategories,
    })
    
def delete_products(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('view_products')  # change redirect as needed
    else:
        messages.error(request, "Invalid request method.")
        return redirect('view_products')


def delivery_boy_list(request):
    pending_boys = DeliveryAgent.objects.filter(status='pending')
    approved_boys = DeliveryAgent.objects.filter(status='approved')
    rejected_boys = DeliveryAgent.objects.filter(status='rejected')
    return render(request, 'delivery_boy_list.html', {
        'pending_boys': pending_boys,
        'approved_boys': approved_boys,
        'rejected_boys': rejected_boys
    })

# # Approve a delivery boy
# def approve_delivery_boy(request):
#     if request.method == 'POST':
#         boy_id = request.POST.get('delivery_boy_id')
#         delivery_boy = get_object_or_404(DeliveryAgent, id=boy_id)
#         delivery_boy.status = 'approved'
#         delivery_boy.save()
#         messages.success(request, f"Delivery boy '{delivery_boy.username}' approved successfully.")
#     return redirect('delivery_boy_list')

# # Reject a delivery boy
# def reject_delivery_boy(request):
#     if request.method == 'POST':
#         boy_id = request.POST.get('delivery_boy_id')
#         delivery_boy = get_object_or_404(DeliveryAgent, id=boy_id)
#         delivery_boy.status = 'rejected'
#         delivery_boy.save()
#         messages.warning(request, f"Delivery boy '{delivery_boy.username}' rejected successfully.")
#     return redirect('delivery_boy_list')

def approve_delivery_boy(request):
    if request.method == 'POST':
        boy_id = request.POST.get('delivery_boy_id')
        delivery_boy = get_object_or_404(DeliveryAgent, id=boy_id)

        delivery_boy.status = 'approved'
        delivery_boy.is_approved = True  # ✅ Set boolean flag
        delivery_boy.save()

        messages.success(request, f"Delivery boy '{delivery_boy.username}' approved successfully.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


# Reject a delivery boy
def reject_delivery_boy(request):
    if request.method == 'POST':
        boy_id = request.POST.get('delivery_boy_id')
        delivery_boy = get_object_or_404(DeliveryAgent, id=boy_id)

        delivery_boy.status = 'rejected'
        delivery_boy.is_approved = False  # ✅ Set boolean flag
        delivery_boy.save()

        messages.warning(request, f"Delivery boy '{delivery_boy.username}' rejected successfully.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


def assign_orders(request):
    # ✅ Show only orders with status = "order placed"
    orders = Order.objects.filter(status="order placed").select_related("user")
    delivery_agents = DeliveryAgent.objects.filter(is_approved=True)
    return render(request, "assign_orders.html", {
        "orders": orders,
        "delivery_agents": delivery_agents,
    })
    
    

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings



def assign_delivery_agent(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        agent_id = request.POST.get("delivery_agent_id")

        if agent_id:
            delivery_agent = get_object_or_404(DeliveryAgent, id=agent_id)
            
            # ✅ assign agent correctly
            order.assigned_agent = delivery_agent
            order.status = "order on the way"
            order.save()

            # ✅ Render HTML email
            subject = "🚚 Your Order is On the Way!"
            context = {
                "user": order.user,
                "order": order,
                "delivery_agent": delivery_agent,
            }
            html_content = render_to_string("order_on_the_way.html", context)
            text_content = f"Hi {order.user.username}, your order #{order.id} is on the way!"

            # ✅ Send HTML email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            messages.success(
                request,
                f"Order #{order.id} assigned to {delivery_agent.username}. Email sent to user."
            )

        return redirect("assign_orders")
    
    
# def doctor_list(request):
#     pending_doctors = Doctor.objects.filter(status='pending')
#     approved_doctors = Doctor.objects.filter(status='approved')
#     rejected_doctors = Doctor.objects.filter(status='rejected')

#     context = {
#         'pending_doctors': pending_doctors,
#         'approved_doctors': approved_doctors,
#         'rejected_doctors': rejected_doctors
#     }
#     return render(request,'doctor_list.html', context)


def approve_doctor(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        doctor = get_object_or_404(Doctor, id=doctor_id)
        doctor.status = 'approved'
        doctor.is_approved = True
        doctor.save()
        messages.success(request, f"Doctor {doctor.full_name} has been approved successfully.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


def reject_doctor(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        doctor = get_object_or_404(Doctor, id=doctor_id)
        doctor.status = 'rejected'
        doctor.is_approved = False
        doctor.save()
        messages.error(request, f"Doctor {doctor.full_name} has been rejected.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


# def admin_view_orders(request):
#     orders = Order.objects.all().order_by('-order_date')
#     return render(request, 'admin/view_orders.html', {'orders': orders})

def admin_view_orders(request):
    orders = Order.objects.exclude(status='pending').order_by('-order_date')
    return render(request, 'view_orders.html', {'orders': orders})

def pending_delivery_agents(request):
    pending_boys = DeliveryAgent.objects.filter(status='pending')

    return render(request, 'pending_delivery_agents.html', {
        'pending_boys': pending_boys
    })

def approved_delivery_agents(request):
    approved_boys = DeliveryAgent.objects.filter(status='approved')

    return render(request, 'approved_delivery_agents.html', {
        'approved_boys': approved_boys
    })

def rejected_delivery_agents(request):
    rejected_boys = DeliveryAgent.objects.filter(status='rejected')

    return render(request, 'rejected_delivery_agents.html', {
        'rejected_boys': rejected_boys
    })


def pending_doctors(request):
    pending_doctors = Doctor.objects.filter(status='pending')
    return render(request, 'pending_doctors.html', {'pending_doctors': pending_doctors})

def approved_doctors(request):
    approved_doctors = Doctor.objects.filter(status='approved')
    return render(request, 'approved_doctors.html', {'approved_doctors': approved_doctors})

def rejected_doctors(request):
    rejected_doctors = Doctor.objects.filter(status='rejected')
    return render(request, 'rejected_doctors.html', {'rejected_doctors': rejected_doctors})


def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()  # using related_name="items"

    return render(request, 'order_detail.html', {
        'order': order,
        'items': items,
    })
    
    
from django.core.paginator import Paginator


def admin_feedback_complaint_view(request):

    # Which tab to show (feedback or complaint)
    tab = request.GET.get("tab", "feedback")

    # Fetch Feedbacks
    feedbacks = Feedback.objects.select_related(
        "appointment__pet__user",
        "appointment__doctor",
        "appointment__slot"
    ).all().order_by("-created_at")

    # Fetch Complaints
    complaints = Complaint.objects.select_related(
        "appointment__pet__user",
        "appointment__doctor"
    ).all().order_by("-created_at")

    # Pagination
    fb_paginator = Paginator(feedbacks, 10)
    cp_paginator = Paginator(complaints, 10)

    fb_page = fb_paginator.get_page(request.GET.get("fb_page", 1))
    cp_page = cp_paginator.get_page(request.GET.get("cp_page", 1))

    return render(request, "admin_feedback_complaint.html", {
        "tab": tab,
        "feedbacks_page": fb_page,
        "complaints_page": cp_page,
    })

def add_product_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('productcategory')

        # Check if category already exists
        if ProductCategory.objects.filter(productcategory__iexact=category_name).exists():
            messages.warning(request, "This product category already exists.")
            return redirect('add_product_category')

        # Save new category
        ProductCategory.objects.create(productcategory=category_name)
        messages.success(request, f"Product category '{category_name}' added successfully!")
        return redirect('add_product_category')

    # Show all existing categories
    categories = ProductCategory.objects.all().order_by('-id')
    return render(request, 'add_product_category.html', {'categories': categories})


@csrf_exempt
def get_doctor_feedback(request, doctor_id=None):
    """API to get feedback for a specific doctor or all doctors"""
    try:
        if doctor_id:
            # Get feedback for specific doctor from Feedback model
            doctor = Doctor.objects.get(id=doctor_id)
            feedbacks = Feedback.objects.filter(appointment__doctor=doctor).order_by('-created_at')
        else:
            # Get feedback for all doctors from Feedback model
            feedbacks = Feedback.objects.all().order_by('-created_at')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(feedbacks, 10)  # 10 items per page
        feedback_page = paginator.get_page(page)
        
        feedback_list = []
        for feedback in feedback_page:
            # Get doctor information from appointment
            doctor = feedback.appointment.doctor if feedback.appointment else None
            
            # Get user information
            user_name = feedback.user_name
            if feedback.appointment and feedback.appointment.pet and feedback.appointment.pet.user:
                user_name = feedback.appointment.pet.user.username
            
            feedback_list.append({
                'id': feedback.id,
                'doctor_id': doctor.id if doctor else None,
                'doctor_name': doctor.full_name if doctor else 'Unknown Doctor',
                'user_name': user_name,
                'rating': feedback.rating,
                'rating_display': feedback.get_rating_display(),
                'feedback': feedback.feedback,
                'created_at': feedback.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        response_data = {
            'success': True,
            'feedbacks': feedback_list,
            'total_pages': paginator.num_pages,
            'current_page': feedback_page.number,
            'has_next': feedback_page.has_next(),
            'has_previous': feedback_page.has_previous(),
        }
        
        return JsonResponse(response_data)
        
    except Doctor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Doctor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def get_doctor_complaints(request, doctor_id=None):
    """API to get complaints for a specific doctor or all doctors"""
    try:
        if doctor_id:
            # Get complaints for specific doctor
            doctor = Doctor.objects.get(id=doctor_id)
            complaints = DoctorComplaint.objects.filter(doctor=doctor).order_by('-created_at')
        else:
            # Get complaints for all doctors
            complaints = DoctorComplaint.objects.all().order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            complaints = complaints.filter(status=status_filter)
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(complaints, 10)  # 10 items per page
        complaints_page = paginator.get_page(page)
        
        complaints_list = []
        for complaint in complaints_page:
            complaints_list.append({
                'id': complaint.id,
                'doctor_id': complaint.doctor.id,
                'doctor_name': complaint.doctor.full_name,
                'user_name': complaint.user_name,
                'complaint': complaint.complaint,
                'status': complaint.status,
                'admin_notes': complaint.admin_notes,
                'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'resolved_at': complaint.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if complaint.resolved_at else None,
            })
        
        response_data = {
            'success': True,
            'complaints': complaints_list,
            'total_pages': paginator.num_pages,
            'current_page': complaints_page.number,
            'has_next': complaints_page.has_next(),
            'has_previous': complaints_page.has_previous(),
        }
        
        return JsonResponse(response_data)
        
    except Doctor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Doctor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def update_complaint_status(request, complaint_id):
    """API to update the status of a doctor complaint"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        status = data.get('status')
        admin_notes = data.get('admin_notes', '')
        
        if status not in ['pending', 'resolved', 'dismissed']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status. Must be one of: pending, resolved, dismissed'
            }, status=400)
        
        complaint = DoctorComplaint.objects.get(id=complaint_id)
        complaint.status = status
        complaint.admin_notes = admin_notes
        
        if status == 'resolved' and not complaint.resolved_at:
            from django.utils import timezone
            complaint.resolved_at = timezone.now()
        elif status != 'resolved':
            complaint.resolved_at = None
            
        complaint.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Complaint status updated to {status}',
            'complaint': {
                'id': complaint.id,
                'status': complaint.status,
                'admin_notes': complaint.admin_notes,
                'resolved_at': complaint.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if complaint.resolved_at else None,
            }
        })
        
    except DoctorComplaint.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Complaint not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def submit_doctor_feedback(request):
    """API to submit feedback for a doctor"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        doctor_id = data.get('doctor_id')
        user_name = data.get('user_name')
        rating = data.get('rating')
        feedback = data.get('feedback')
        
        # Validate required fields
        if not all([doctor_id, user_name, rating, feedback]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: doctor_id, user_name, rating, feedback'
            }, status=400)
        
        # Validate rating
        if rating not in [1, 2, 3, 4, 5]:
            return JsonResponse({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }, status=400)
        
        doctor = Doctor.objects.get(id=doctor_id)
        
        # Create feedback
        doctor_feedback = DoctorFeedback.objects.create(
            doctor=doctor,
            user_name=user_name,
            rating=rating,
            feedback=feedback
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Feedback submitted successfully',
            'feedback_id': doctor_feedback.id,
            'created_at': doctor_feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Doctor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Doctor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)