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
router.register(r"delivery_registration",DeliveryBoyRegistrationView),

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
    path('login/', DeliveryBoyLoginAPI.as_view(), name='delivery_login'),
    path('view_profile/', DeliveryBoyProfileView.as_view(), name='view_delivery_agent_profile'),
    path("confirm_delivery/", ConfirmDeliveryView.as_view(), name="confirm_delivery"),
    path('assigned_orders/', AssignedOnTheWayOrdersView.as_view(), name='assigned_orders'),
    path('order_detail/', OrderDetailView.as_view(), name='order_detail'),
]