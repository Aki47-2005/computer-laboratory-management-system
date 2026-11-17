from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('login/', views.login_page, name='login'),

    path('labs/', views.labs, name='labs'),
    path('labs/edit/<int:id>/', views.edit_lab, name='edit_lab'),
    path('labs/delete/<int:id>/', views.delete_lab, name='delete_lab'),

    path('computers/', views.computers, name='computers'),
    path('computers/edit/<int:id>/', views.edit_computer, name='edit_computer'),
    path('computers/delete/<int:id>/', views.delete_computer, name='delete_computer'),

    path('specifications/', views.specifications, name='specifications'),
    path('specifications/edit/<int:id>/', views.edit_specification, name='edit_specification'),
    path('specifications/delete/<int:id>/', views.delete_specification, name='delete_specification'),

    path('instructor/', views.instructors, name='instructor'),
    path('instructor/edit/<int:id>/', views.edit_instructor, name='edit_instructor'),
    path('instructor/delete/<int:id>/', views.delete_instructor, name='delete_instructor'),

    path('schedules/', views.schedules, name='schedules'),
    path('schedules/edit/<int:id>/', views.edit_schedule, name='edit_schedule'),
    path('schedules/delete/<int:id>/', views.delete_schedule, name='delete_schedule'),

    path('attendants/', views.attendants, name='attendants'),
    path('attendants/edit/<int:id>/', views.edit_attendant, name='edit_attendant'),
    path('attendants/delete/<int:id>/', views.delete_attendant, name='delete_attendant'),

    path('maintenance/', views.maintenance, name='maintenance'),
    path('maintenance/edit/<int:id>/', views.edit_maintenance, name='edit_maintenance'),
    path('maintenance/delete/<int:id>/', views.delete_maintenance, name='delete_maintenance'),

    path('disposals/', views.disposals, name='disposals'),
    path('disposals/edit/<int:id>/', views.edit_disposal, name='edit_disposal'),
    path('disposals/delete/<int:id>/', views.delete_disposal, name='delete_disposal'),

    path('signup/', views.signup_page, name='signup'),
    path('logout/', views.logout_page, name='logout'),
]
