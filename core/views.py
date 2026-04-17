from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.models import Profile
from core.serializers import ProfileSerializer
from core.services import ExternalAPIError, agify, genderize, nationalize


def _error(message, status_code):
    return Response({"status": "error", "message": message}, status=status_code)


class ProfileListCreateView(APIView):
    def post(self, request, *args, **kwargs):
        if "name" not in request.data:
            return _error("'name' is required", status.HTTP_400_BAD_REQUEST)

        name = request.data.get("name")

        if not isinstance(name, str):
            return _error("'name' must be a string", status.HTTP_422_UNPROCESSABLE_ENTITY)

        name = name.strip()
        if not name:
            return _error("'name' cannot be empty", status.HTTP_400_BAD_REQUEST)

        existing = Profile.objects.filter(name__iexact=name).first()
        if existing:
            return Response(
                {
                    "status": "success",
                    "message": "Profile already exists",
                    "data": ProfileSerializer(existing).data,
                },
                status=status.HTTP_200_OK,
            )

        try:
            enrichment = {
                **genderize(name),
                **agify(name),
                **nationalize(name),
            }
        except ExternalAPIError as exc:
            return _error(exc.message, status.HTTP_502_BAD_GATEWAY)

        profile = Profile.objects.create(name=name, **enrichment)
        return Response(
            {"status": "success", "data": ProfileSerializer(profile).data},
            status=status.HTTP_201_CREATED,
        )

    def get(self, request, *args, **kwargs):
        queryset = Profile.objects.all().order_by("-created_at")
        for field in ("gender", "country_id", "age_group"):
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{f"{field}__iexact": value})

        serialized = ProfileSerializer(queryset, many=True).data
        return Response(
            {"status": "success", "count": len(serialized), "data": serialized},
            status=status.HTTP_200_OK,
        )


class ProfileDetailView(APIView):
    def _get_object(self, id):
        try:
            return Profile.objects.get(pk=id)
        except Profile.DoesNotExist:
            return None

    def get(self, request, id, *args, **kwargs):
        profile = self._get_object(id)
        if profile is None:
            return _error("Profile not found", status.HTTP_404_NOT_FOUND)
        return Response(
            {"status": "success", "data": ProfileSerializer(profile).data},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id, *args, **kwargs):
        profile = self._get_object(id)
        if profile is None:
            return _error("Profile not found", status.HTTP_404_NOT_FOUND)
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
