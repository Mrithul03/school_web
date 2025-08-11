from django.urls import path
from .views import login_user,current_user_profile,update_location,get_latest_location,students_list,get_student_routes,vehicle_location

urlpatterns = [
    path('api/login/', login_user, name='login_user'),
    path('api/user/me/', current_user_profile),
    path('api/update_location/', update_location),
    path('api/vehicle/<int:vehicle_id>/location/', get_latest_location),
    path('api/students/', students_list, name='students-list'),
    path('api/locations_list/', vehicle_location, name='locations_list'),
    path('api/student_routes/<int:vehicle_id>/', get_student_routes, name='student-routes'),


]
