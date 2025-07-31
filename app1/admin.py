from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    School, Vehicle, Student, Shift,
    Route, Payment, UserProfile
)

# Inline to show UserProfile inside User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_select_related = ('userprofile',)

    def get_role(self, instance):
        return instance.userprofile.role if hasattr(instance, 'userprofile') else '-'
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_code', 'contact_number')
    search_fields = ('name', 'school_code')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'driver', 'capacity', 'number_of_trip')
    search_fields = ('vehicle_number', 'driver')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'school', 'parent')
    list_filter = ('school',)
    search_fields = ('name', 'phone')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'school', 'vehicle')
    list_filter = ('role', 'school')
    search_fields = ('user__username', 'phone')

# Optional: register other models
admin.site.register(Shift)
admin.site.register(Route)
admin.site.register(Payment)
