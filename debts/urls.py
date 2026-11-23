from django.urls import path
from . import views

urlpatterns = [
    path('people/', views.person_list, name='person_list'),
    path('people/<int:pk>/delete/', views.person_delete, name='person_delete'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<int:pk>/repay/', views.repayment_create, name='repayment_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
]