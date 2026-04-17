from django.urls import path

from core.views import ProfileDetailView, ProfileListCreateView

urlpatterns = [
    path("profiles", ProfileListCreateView.as_view(), name="profile-list-create"),
    path("profiles/<uuid:id>", ProfileDetailView.as_view(), name="profile-detail"),
]
