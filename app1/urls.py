from django.urls import path
from .views import login_user,current_user_profile,update_location,get_latest_location,students_list,get_student_routes,vehicle_location,update_student_location,create_payment,get_payments

urlpatterns = [
    path('api/login/', login_user, name='login_user'),
    path('api/user/me/', current_user_profile),
    path('api/update_location/', update_location),
    path('api/vehicle/<int:vehicle_id>/location/', get_latest_location),
    path('api/students/<int:vehicle_id>/', students_list, name='students-list'),
    path('api/locations_list/', vehicle_location, name='locations_list'),
    path('api/student_routes/<int:vehicle_id>/', get_student_routes, name='student-routes'),
    path('api/student/<int:student_id>/update-location/', update_student_location, name='update-student-location'),
    path("api/payment/", create_payment, name="create_payment"),
    path("api/payment-list/", get_payments, name="get_payments"),


]
