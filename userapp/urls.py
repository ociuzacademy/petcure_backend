from django.urls import path
from django.urls import path, re_path,include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from .views import *

schema_view = get_schema_view(
    openapi.Info(
        title="PETCURE API",
        default_version="v1",
        description="API documentation for the PETCURE system.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@PETCURE.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],

)

router = DefaultRouter()
router.register(r"user_registration",UserRegistrationView),
router.register(r'category_products', ProductViewSet, basename='category_products')

urlpatterns = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path("",include(router.urls)),
    path('login/', LoginView.as_view(), name='user_login'),
    path('view_profile/',UserProfileView.as_view({'get':'list'}),name='view_profile'),
    path('update_profile/',UpdateUserProfileView.as_view(),name='update_profile'),
    path('view_pet_category/',ViewPetCategoryView.as_view({'get':'list'}),name='view_pet_category'),
    path('view_pet_subcategory/',ViewPetSubCategoryView.as_view({'get':'list'}),name='view_pet_subcategory'),
    path('add_pet/', AddPetAPIView.as_view(), name='add-pet'),
    path('user_pets/', UserPetsListAPIView.as_view(), name='user_pets'),
    path('pet_details/', PetDetailAPIView.as_view(), name='pet_details'),
    path('update_pet_details/', UpdatePetDetailsView.as_view(), name='update_pet_details'),
    path('view_all_products/', ViewAllProductsView.as_view(), name='view_all_products'),
    path('product_details/', ProductDetailsView.as_view(), name='product_details'),
    path('add_to_cart/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart_items/', CartItemListView.as_view(), name='cart_items'),
    path('update_cart_quantity/', UpdateCartQuantityByIdView.as_view(), name='update_cart_quantity'),
    path('make_purchase/', MakePurchaseView.as_view(), name='make_purchase'),
    path('buy_now/', BuyNowView.as_view(), name='buy_now'),
    path('upi-payment/', UPIPaymentView.as_view(), name='upi-payment'),
    path('card-payment/', CardPaymentView.as_view(), name='card-payment'),
    path('remove_cart_item/', RemoveCartView.as_view(), name='remove_cart_item'),
    path('remove_all_cart_items/', ClearCartView.as_view(), name='remove_all_cart_items/'),
    path('cancel-order/', CancelOrderView.as_view(), name='cancel_order'),
    path('orders-list/', OrderListView.as_view(), name='orders-list'),
    path('order-details/', OrderDetailView.as_view(), name='order-details'),
    path('nearby_doctors/', NearbyDoctorsView.as_view(), name='nearby_doctors'),
    path('view_slots/', DoctorSlotListView.as_view(), name='doctor_slots'),
    path('book_appointment/', AppointmentBookingView.as_view(), name='book_appointment'),
    path('pet_appointments/', PetBookingListView.as_view(), name='pet_appointments'),
    path('reorder/', ReorderAPIView.as_view(), name='reorder'),
]
