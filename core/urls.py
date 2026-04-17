from django.urls import path
from core.views import ProfileCreateView 



urlpatterns = [
    path('profiles', ProfileCreateView.as_view(), name='create-profile')
]

