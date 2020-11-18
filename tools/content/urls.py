from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.parse_content, name='parse_content'),
]
