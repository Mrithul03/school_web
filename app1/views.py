from django.shortcuts import render, redirect
from django.views import View

from .models import UserProfile,School,Student,VehicleLocation,Vehicle,StudentRoute,Payment
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
import requests
from django.contrib import messages
from rest_framework.authentication import TokenAuthentication
from django.http import JsonResponse
from django.utils import timezone
import json
from decimal import Decimal
from django.utils.timezone import now
from django.utils.dateparse import parse_date

import json
from google.oauth2 import service_account
from google.auth.transport import requests
from django.http import JsonResponse
from django.conf import settings


# === Firebase Setup ===
SERVICE_ACCOUNT_FILE = 'app1/school-manager-aeaf5-firebase-adminsdk-fbsvc-c962269990.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

def get_access_token():
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

def send_fcm_notification(device_token, title, body):
    fcm_url = 'https://fcm.googleapis.com/v1/projects/blueeyes-a1413/messages:send'

    message = {
        "message": {
            "token": device_token,
            "notification": {
                "title": title,
                "body": body
            }
        }
    }

    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json; UTF-8'
    }

    response = requests.post(fcm_url, headers=headers, data=json.dumps(message))
    if response.status_code == 200:
        print(" Notification sent successfully")
    else:
        print(f"Error sending notification: {response.status_code}, {response.text}")

# Create your views here.

@api_view(["PATCH"])
@permission_classes([AllowAny])  # Parents not logged in yet
def parent_register(request):
    phone = request.data.get("phone")
    password = request.data.get("password")
    parent_name = request.data.get("parent_name")
    student_name = request.data.get("student_name")

    if not phone:
        return Response(
            {"error": "Phone number is required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1. Check phone exists in UserProfile
    try:
        profile = UserProfile.objects.get(phone=phone, role="parent")
    except UserProfile.DoesNotExist:
        return Response(
            {"error": "Phone number not found. Please contact school."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = profile.user

    # 2. Update password
    if password:
        user.set_password(password)
        user.save()

    # 3. Find student linked by parent's phone
    student = Student.objects.filter(phone=phone).first()

    if not student:
        return Response(
            {"error": "No student linked to this parent."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4. Update details
    if student_name:
        student.name = student_name
    if parent_name:
        student.parent = parent_name  # updates the `parent` CharField
    student.save()

    return Response(
        {"success": True, "message": "Registration completed successfully."},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    school_code = request.data.get('school_code')
    phone =  request.data.get('phone')
    password = request.data.get('password')
    role = request.data.get('role')  
    fcm_token = request.data.get('fcm_token')  # 👈 Get FCM token from frontend

    print(f" Login attempt:school_code={school_code} phone={phone}, password={password}")

    try:
        profile = UserProfile.objects.get(phone=phone)
        user = profile.user

        #  Check if school_code matches
        school = School.objects.get(school_code=school_code)

        # Now check if the user’s school matches this instance
        if profile.school != school:
            return Response({'error': 'User does not belong to this school'}, status=401)

        #  Check password
        if not user.check_password(password):
            print(" Invalid password")
            return Response({'error': 'Invalid password'}, status=401)
        
        #  Role check
        if role and profile.role.lower() != role.lower():
            print("Role mismatch")
            return Response({'error': f'User is not a {role}'}, status=401)

        #  Clear previous tokens
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        if profile.role == 'parent':
            try:
        # Check if already linked student has the same phone
                if profile.student and profile.student.phone == phone:
                    print(f" Already linked to student ID: {profile.student.id}")
                else:
            # Try to find a new matching student
                    matched_student = Student.objects.get(phone=phone)
                    profile.student = matched_student
                    profile.save()
                    print(f" Linked to new student ID: {matched_student.id}")
            except Student.DoesNotExist:
                profile.student = None
                print("ℹ No matching student found for this phone")

        if fcm_token:
            profile.fcm_token = fcm_token
        profile.save()

        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user_id': user.id,
            'name': user.username,
            'phone': profile.phone,
            'role': profile.role,
            'vehicle': {
        'id': profile.vehicle.id if profile.vehicle else None,
        'vehicle_number': profile.vehicle.vehicle_number if profile.vehicle else None,
    },
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        print(" UserProfile not found")
        return Response({'error': 'User does not exist'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_vehicle_location(request):
    lat = request.data.get('latitude')
    lon = request.data.get('longitude')
    vehicle_id = request.data.get('vehicle_id')
    
    vehicle = Vehicle.objects.get(id=vehicle_id)
    VehicleLocation.objects.update_or_create(
        vehicle=vehicle,
        defaults={'latitude': lat, 'longitude': lon}
    )
    return Response({"status": "Location updated"})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user_profile(request):
    try:
        user = request.user
        profile = UserProfile.objects.select_related('school', 'vehicle', 'student').get(user=user)

        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': profile.phone,
            'role': profile.role,
            'school': {
                'id': profile.school.id if profile.school else None,
                'name': profile.school.name if profile.school else None,
            },
            'vehicle': {
                'id': profile.vehicle.id if profile.vehicle else None,
                'vehicle_number': profile.vehicle.vehicle_number if profile.vehicle else None,
                'driver' :profile.vehicle.driver if profile.vehicle else None,
                'phone' : profile.vehicle.phone if profile.vehicle else None,
            },
            'student': {
                'id': profile.student.id if profile.student else None,
                'name': profile.student.name if profile.student else None,
                'parent': profile.student.parent if profile.student else None,
                'home_lat':profile.student.home_lat if profile.student else None,
                'home_lng':profile.student.home_lng if profile.student else None,

            }
        }

        return JsonResponse(data)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'UserProfile not found'}, status=404)
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def students_list(request, vehicle_id):
    try:
        students = Student.objects.select_related('school', 'vehicle') \
                                   .filter(vehicle_id=vehicle_id)

        data = []
        for student in students:
            data.append({
                'id': student.id,
                'name': student.name,
                'parent': student.parent,
                'phone': student.phone,
                'school': {
                    'id': student.school.id if student.school else None,
                    'name': student.school.name if student.school else None,
                },
                'vehicle': {
                    'id': student.vehicle.id if student.vehicle else None,
                    'vehicle_number': student.vehicle.vehicle_number if student.vehicle else None,
                    'driver': student.vehicle.driver if student.vehicle and hasattr(student.vehicle, 'driver') else None,
                }
            })

        return JsonResponse(data, safe=False)  #  moved outside loop

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def vehicle_location(request):
    try:
        location = VehicleLocation.objects.select_related('vehicle').latest('updated_at')
        data = {
            'id': location.id,
            'vehicle_id': location.vehicle.id,
            'vehicle_name': str(location.vehicle),
            'latitude': location.latitude,
            'longitude': location.longitude,
            'updated_at': location.updated_at,
            'ride_start': location.ride_start,
            'ride_stop': location.ride_stop,
            'status': location.status,
        }
        return JsonResponse(data)
    except VehicleLocation.DoesNotExist:
        return JsonResponse({'error': 'location not found'}, status=404)


# @api_view(['POST'])
# @permission_classes([AllowAny])
# def update_location(request):
#     try:
#         data = request.data
#         print(" Incoming location data:", data)

#         action = data.get("action")  # expected: 'start' or 'stop'
#         status = "running" if action == "start" else "stopped"

#         vehicle = Vehicle.objects.get(id=data['vehicle_id'])

#         # Save location
#         VehicleLocation.objects.create(
#             vehicle=vehicle,
#             latitude=data['latitude'],
#             longitude=data['longitude'],
#             status=status
#         )

#         #  Notify all parents if tracking starts
#         if action == "start":
#             students = Student.objects.filter(vehicle=vehicle)
#             parent_profiles = UserProfile.objects.filter(student__in=students, role="parent")

#             # Send notification to each parent individually
#             for parent in parent_profiles:
#                 if parent.fcm_token:
#                     send_fcm_notification(
#                         parent.fcm_token,
#                         "Tracking Started",
#                         f"Your child's bus {vehicle.vehicle_number} is now being tracked 🚍"
#                     )

#         return Response({"success": True, "status": status})

#     except Vehicle.DoesNotExist:
#         return Response({"success": False, "error": "Vehicle not found"}, status=404)
#     except Exception as e:
#         print(" Exception occurred:", e)
#         return Response({"success": False, "error": str(e)}, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def update_location(request):
    try:
        data = request.data
        print(" Incoming location data:", data)

        # Determine status automatically based on an "action" key
        action = data.get("action")  # expected values: 'start' or 'stop'
        status = "running" if action == "start" else "stopped"

        VehicleLocation.objects.create(
            vehicle_id=data['vehicle_id'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            status=status
        )
        return Response({"success": True, "status": status})
    except Exception as e:
        print(" Exception occurred:", e)
        return Response({"success": False, "error": str(e)}, status=500)

    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_location(request, vehicle_id):
    try:
        latest_location = VehicleLocation.objects.filter(vehicle_id=vehicle_id).latest('updated_at')
        return Response({
            "latitude": latest_location.latitude,
            "longitude": latest_location.longitude,
            "status": latest_location.status,
            "updated_at": latest_location.updated_at
        })
    except VehicleLocation.DoesNotExist:
        return Response({"error": "No location data found"}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_student_routes(request, vehicle_id):
    try:
        routes = StudentRoute.objects.select_related('student', 'vehicle', 'school') \
                                     .filter(vehicle_id=vehicle_id)

        if not routes.exists():
            return JsonResponse({'error': 'No routes found for this vehicle'}, status=404)

        data = []
        for route in routes:
            data.append({
                'id' : route.id,
                'student': {
                    'id': route.student.id,
                    'phone':route.student.phone,
                    'name': route.student.name,
                    'home_lat': route.student.home_lat,
                    'home_lng': route.student.home_lng,
                    'parent': route.student.parent,
                },
                'vehicle': {
                    'id': route.vehicle.id if route.vehicle else None,
                    'vehicle_number': route.vehicle.vehicle_number if route.vehicle else None,
                    'driver': getattr(route.vehicle, 'driver', None) if route.vehicle else None,
                },
                'school': {
                    'id': route.school.id if route.school else None,
                    'name': route.school.name if route.school else None,
                },
                'shift': route.shift,
                'trip_number': route.trip_number,
                'route_order': route.route_order,
            })

        return JsonResponse(data, safe=False)  # safe=False allows list output
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])  # remove if not needed
def update_student_location(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    home_lat = request.data.get('home_lat')
    home_lng = request.data.get('home_lng')

    if home_lat is None or home_lng is None:
        return JsonResponse({"error": "home_lat and home_lng are required"}, status=400)

    student.home_lat = home_lat
    student.home_lng = home_lng
    student.save()

    return JsonResponse({
        "message": "Student location updated successfully",
        "student": {
            "id": student.id,
            "name": student.name,
            "home_lat": student.home_lat,
            "home_lng": student.home_lng
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    try:
        data = request.data

        student_id = data.get("student_id")
        month = data.get("month")   # Expecting integer 1-12
        year = data.get("year")     # Expecting integer year, e.g., 2025
        amount = data.get("amount")
        is_paid = data.get("is_paid", False)

        if not student_id or not month or not amount or not year:
            return JsonResponse({"error": "student_id, month, year, and amount are required"}, status=400)

        student = Student.objects.get(id=student_id)

        # ✅ Check if payment already exists
        existing_payment = Payment.objects.filter(
            student=student,
            month=int(month),
            year=int(year),
            is_paid=True  # only block if already marked paid
        ).first()

        if existing_payment:
            return JsonResponse(
                {"error": f"Payment already exists for {student.name}, {month}/{year}"},
                status=400
            )

        # ✅ Create new payment
        payment = Payment.objects.create(
            student=student,
            month=int(month),
            year=int(year),
            amount=Decimal(amount),
            is_paid=is_paid,
            paid_on=data.get("paid_on") if is_paid and data.get("paid_on") else None
        )

        return JsonResponse({
            "id": payment.id,
            "student": payment.student.name,
            "month": payment.get_month_display(),
            "year": payment.year,
            "amount": str(payment.amount),
            "is_paid": payment.is_paid,
            "paid_on": str(payment.paid_on) if payment.paid_on else None,
        }, status=201)

    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_payments(request):
    try:
        profile = UserProfile.objects.select_related("student").get(user=request.user)

        if not profile.student:
            return Response({"error": "No student linked to this user."}, status=400)

        payments = Payment.objects.filter(student=profile.student).values(
            "id",
            "student_id",
            "month",
            "year",
            "amount",
            "is_paid",
            "paid_on"
        )
        return Response(list(payments))

    except UserProfile.DoesNotExist:
        return Response({"error": "UserProfile not found"}, status=404)



# @api_view(['PATCH'])   # PATCH → partial update (only send changed fields)
# @permission_classes([IsAuthenticated])
# def edit_payment(request, payment_id):
#     try:
#         payment = Payment.objects.get(id=payment_id)

#         data = request.data

#         # Update fields only if provided
#         if "student_id" in data:
#             try:
#                 student = Student.objects.get(id=data["student_id"])
#                 payment.student = student
#             except Student.DoesNotExist:
#                 return JsonResponse({"error": "Student not found"}, status=404)

#         if "month" in data:
#             payment.month = parse_date(data["month"])

#         if "amount" in data:
#             payment.amount = Decimal(data["amount"])

#         if "is_paid" in data:
#             payment.is_paid = bool(data["is_paid"])
#             if payment.is_paid and "paid_on" in data:
#                 payment.paid_on = parse_date(data["paid_on"])
#             elif not payment.is_paid:
#                 payment.paid_on = None  # reset if unpaid

#         payment.save()

#         return JsonResponse({
#             "id": payment.id,
#             "student": payment.student.name if payment.student else None,
#             "month": payment.month.strftime("%B %Y") if payment.month else None,
#             "amount": str(payment.amount),
#             "is_paid": payment.is_paid,
#             "paid_on": str(payment.paid_on) if payment.paid_on else None,
#         })

#     except Payment.DoesNotExist:
#         return JsonResponse({"error": "Payment not found"}, status=404)

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=400)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_route_order(request, route_id):
    try:
        route = StudentRoute.objects.get(id=route_id)
        data = request.data

        updated = False

        if "route_order" in data:
            route.route_order = data["route_order"]
            updated = True

        if "trip_number" in data:
            route.trip_number = data["trip_number"]
            updated = True

        if updated:
            route.save()
        else:
            return JsonResponse({"error": "No valid fields to update"}, status=400)

        return JsonResponse({
            "id": route.id,
            "student": route.student.name,
            "vehicle": route.vehicle.vehicle_number,
            "school": route.school.name,
            "shift": route.shift,
            "trip_number": route.trip_number,
            "route_order": route.route_order,
        })

    except StudentRoute.DoesNotExist:
        return JsonResponse({"error": "Route not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

