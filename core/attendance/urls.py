from django.urls import path
from django.contrib.auth import views as auth_views
from . import views # Ye 'attendance' folder ke views ko load karega

urlpatterns = [
    path('', views.home, name='home'),
    path('download/<str:filename>/', views.download_csv, name='download_csv'),
    path('students/', views.view_students, name='view_students'),
    path('register-student/', views.register_student, name='register_student'),
    path('mark-attendance/', views.mark_attendance_view, name='mark_attendance'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register-account/', views.register_account, name='register_account'),
    path('edit-student/<int:pk>/', views.edit_student, name='edit_student'),
    path('delete-student/<int:pk>/', views.delete_student, name='delete_student'),
]