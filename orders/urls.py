from django.urls import path
from . import views

urlpatterns = [
    path('basket/', views.basket_view, name='basket'),
    path('add/<int:book_id>/', views.add_to_basket, name='add_to_basket'),
    path('remove/<int:item_id>/', views.remove_item, name='remove_item'),
    path('update/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('submit/', views.submit_order, name='submit_order'),
    path('history/', views.order_history, name='order_history'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
]
