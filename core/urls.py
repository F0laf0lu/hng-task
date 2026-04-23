from django.urls import path

from core.views import ProfileDetailView, ProfileListCreateView, ProfileSearchView

urlpatterns = [
    path("profiles/search", ProfileSearchView.as_view(), name="profile-search"),
    path("profiles", ProfileListCreateView.as_view(), name="profile-list-create"),
    path("profiles/<uuid:id>", ProfileDetailView.as_view(), name="profile-detail"),
]
