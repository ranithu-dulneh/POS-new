from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_view, name='pos_view'), # Default home to POS for now, or change later
    path('pos/add/', views.pos_add_item, name='pos_add_item'),
    path('pos/remove/<str:product_id>/', views.pos_remove_item, name='pos_remove_item'),
    path('pos/clear/', views.pos_clear, name='pos_clear'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),

    # Online Store placeholders
    path('store/', views.product_list, name='product_list'),
    path('store/product/<int:pk>/', views.product_detail, name='product_detail'),
    path('store/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('store/cart/', views.cart_view, name='cart_view'),
    path('store/cart/remove/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('store/checkout/', views.checkout, name='checkout'),

    # Reports
    path('reports/', views.report_view, name='report_view'),
]
