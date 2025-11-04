from django.shortcuts import render,redirect
from django.contrib import messages
from .models import *
from deliveryapp.models import *
from userapp.models import *
# Create your views here.

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


# Delete Product Category
def delete_product_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = get_object_or_404(ProductCategory, id=category_id)
        category.delete()
        messages.success(request, "Product category deleted successfully!")
        return redirect('add_product_category')
    

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
    return redirect('delivery_boy_list')


# Reject a delivery boy
def reject_delivery_boy(request):
    if request.method == 'POST':
        boy_id = request.POST.get('delivery_boy_id')
        delivery_boy = get_object_or_404(DeliveryAgent, id=boy_id)

        delivery_boy.status = 'rejected'
        delivery_boy.is_approved = False  # ✅ Set boolean flag
        delivery_boy.save()

        messages.warning(request, f"Delivery boy '{delivery_boy.username}' rejected successfully.")
    return redirect('delivery_boy_list')


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
    
    
def doctor_list(request):
    pending_doctors = Doctor.objects.filter(status='pending')
    approved_doctors = Doctor.objects.filter(status='approved')
    rejected_doctors = Doctor.objects.filter(status='rejected')

    context = {
        'pending_doctors': pending_doctors,
        'approved_doctors': approved_doctors,
        'rejected_doctors': rejected_doctors
    }
    return render(request,'doctor_list.html', context)


def approve_doctor(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        doctor = get_object_or_404(Doctor, id=doctor_id)
        doctor.status = 'approved'
        doctor.is_approved = True
        doctor.save()
        messages.success(request, f"Doctor {doctor.full_name} has been approved successfully.")
    return redirect('doctor_list')


def reject_doctor(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        doctor = get_object_or_404(Doctor, id=doctor_id)
        doctor.status = 'rejected'
        doctor.is_approved = False
        doctor.save()
        messages.error(request, f"Doctor {doctor.full_name} has been rejected.")
    return redirect('doctor_list')


def admin_view_orders(request):
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'admin/view_orders.html', {'orders': orders})