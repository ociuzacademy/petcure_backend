from django.urls import path
from.import views
from .views import *

urlpatterns = [
    path('',views.login,name='login'),
    path('admin_index',views.admin_index,name='admin_index'),
    path('logout/',views.logout,name='logout'),
    path('add_pet_category/', add_pet_category, name='add_pet_category'),
    path('edit_pet_category/', views.edit_pet_category, name='edit_pet_category'),
    path('delete_pet_category/', views.delete_pet_category, name='delete_pet_category'),
    path('edit_pet_subcategory/', views.edit_pet_subcategory, name='edit_pet_subcategory'),
    path('delete_pet-subcategory/', views.delete_pet_subcategory, name='delete_pet_subcategory'),
    path('add_product_category/', views.add_product_category, name='add_product_category'),
    path('edit_product_category/', views.edit_product_category, name='edit_product_category'),
    path('deleteproduct_category/', views.delete_product_category, name='delete_product_category'),
    path('add_products/', views.add_products, name='add_products'),
    path('view_products/', views.view_products, name='view_products'),
    path('edit_products/', views.edit_products, name='edit_products'),
    path('delete_products/', views.delete_products, name='delete_products'),
    path('delivery-boys/', views.delivery_boy_list, name='delivery_boy_list'),
    path('delivery-boy/approve/', views.approve_delivery_boy, name='approve_delivery_boy'),
    path('delivery-boy/reject/', views.reject_delivery_boy, name='reject_delivery_boy'),
    path("assign-orders/", views.assign_orders, name="assign_orders"),
    path("assign-orders/<int:order_id>/assign/", views.assign_delivery_agent, name="assign_delivery_agent"),
    path('doctor_list/', views.doctor_list, name='doctor_list'),
    path('approve_doctor/', views.approve_doctor, name='approve_doctor'),
    path('reject_doctor/', views.reject_doctor, name='reject_doctor'),
    
]