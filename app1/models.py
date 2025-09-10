from django.contrib.auth.models import User
from django.db import models
from datetime import date


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('parent', 'Parent'),
        ('driver', 'Driver'),
        ('admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, unique=True)
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True)
    fcm_token = models.CharField(max_length=256, blank=True, null=True)


    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
class School(models.Model):
    name = models.CharField(max_length=100)
    school_code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return self.name
    
class Vehicle(models.Model):
    driver = models.CharField(max_length=20)
    vehicle_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    number_of_trip = models.PositiveIntegerField(default=1)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.vehicle_number
    
# class Shift(models.Model):
#     SHIFT_CHOICES = (
#         ('morning', 'Morning'),
#         ('evening', 'Evening'),
#     )
#     vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
#     school = models.ForeignKey(School, on_delete=models.CASCADE)
#     shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES)
#     start_time = models.TimeField()
#     end_time = models.TimeField()

#     def __str__(self):
#         return f"{self.vehicle} - {self.shift_type}"
    
class Student(models.Model):
    name = models.CharField(max_length=100)
    parent = models.CharField(max_length=123)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle,on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15)
    home_lat = models.DecimalField(max_digits=9, decimal_places=6,null=True, blank=True)
    home_lng = models.DecimalField(max_digits=9, decimal_places=6,null=True, blank=True)

    def __str__(self):
        return self.name
    
class StudentRoute(models.Model):
    SHIFT_CHOICES = (
    ('morning', 'Morning'),
    ('evening', 'Evening'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    trip_number = models.IntegerField()
    route_order = models.PositiveIntegerField(help_text="Order of pickup/drop in the route")

    class Meta:
        unique_together = ('student', 'shift', 'trip_number')

    def __str__(self):
        return f"{self.student.name} - {self.shift} Trip {self.trip_number}"

class Payment(models.Model):
    MONTH_CHOICES = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    month = models.IntegerField(choices=MONTH_CHOICES)  # Accepts 1–12
    year = models.IntegerField(default=date.today().year)  # Integer year
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_on = models.DateField(null=True, blank=True)  #  Optional

    def __str__(self):
        return f"{self.student.name} - {self.get_month_display()} {self.year} - {'Paid' if self.is_paid else 'Pending'}"



class VehicleLocation(models.Model):
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('stopped', 'Stopped'),
    )

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)
    ride_start = models.DateTimeField(null=True, blank=True)
    ride_stop = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='stopped')

    def __str__(self):
        return f"{self.vehicle} - {self.updated_at}"
