# vehicle/routing.py
from django.urls import re_path
from app1 import consumers

websocket_urlpatterns = [
    re_path(r'ws/location/(?P<vehicle_id>\d+)/$', consumers.LocationConsumer.as_asgi()),
]
