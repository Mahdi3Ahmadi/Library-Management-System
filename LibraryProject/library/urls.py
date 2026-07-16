from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('return/<int:borrow_id>/', views.return_book, name='return_book'),
    path('pay-penalty/<int:borrow_id>/', views.pay_penalty, name='pay_penalty'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('cancel-reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
]