from django.contrib.auth.models import User
from django.db import models

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
    student = models.ForeignKey('student',on_delete=models.SET_NULL, null=True, blank=True)

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

    def __str__(self):
        return self.vehicle_number
    
class Shift(models.Model):
    SHIFT_CHOICES = (
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.vehicle} - {self.shift_type}"
    
class Student(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle,on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15)
    trip_number = models.IntegerField()

    def __str__(self):
        return self.name
    
class Route(models.Model):
    shift = models.OneToOneField(Shift, on_delete=models.CASCADE)
    polyline = models.TextField(help_text="Encoded polyline or JSON of LatLngs")
    trip = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='student_trips')

    def __str__(self):
        return f"Route for {self.shift}"

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.DateField()  # Use 1st of month to represent "July 2025"
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_on = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.month.strftime('%B %Y')} - {'Paid' if self.is_paid else 'Pending'}"
