from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_view, name='pos_view'), # Default home to POS for now, or change later
    path('pos/add/', views.pos_add_item, name='pos_add_item'),
    path('pos/remove/<str:product_id>/', views.pos_remove_item, name='pos_remove_item'),
    path('pos/clear/', views.pos_clear, name='pos_clear'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),

    # Management
    path('manage/login/', views.manager_login, name='manager_login'),
    path('manage/', views.manage_dashboard, name='manage_dashboard'),
    path('manage/add/', views.add_product, name='add_product'),
    path('manage/remove/', views.remove_product, name='remove_product'),
    path('manage/remove/<int:pk>/', views.remove_product_action, name='remove_product_action'),
    path('manage/stock/', views.add_stock, name='add_stock'),
    path('manage/stock/<int:pk>/', views.add_stock_action, name='add_stock_action'),

    # Reports
    path('reports/', views.report_view, name='report_view'),
]
