from django.contrib import admin
from django.urls import path
from .views import login_user

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', login_user, name='login_user'),
]
