
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from core.serializers import ProfileSerializer
from core .models import Profile
import requests


def _cors(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "*"
    return response

def _error(message, status_code):
    return _cors(Response({"status": "error", "message": message}, status=status_code))


def genderize(name):
    try:
        api_response = requests.get(
            "https://api.genderize.io/",    
            params={"name": name},
            timeout=10,
        )
        api_response.raise_for_status()
        data = api_response.json()
    except requests.Timeout:
        return _error("Genderize API request timed out", status.HTTP_502_BAD_GATEWAY)
    except requests.RequestException:
        return _error("Failed to reach Genderize API", status.HTTP_502_BAD_GATEWAY)
    except ValueError:
        return _error("Genderize returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    
    gender = data.get("gender")
    probability = data.get("probability")
    sample_size = data.get("count")

    if gender is None or sample_size in (None, 0):
        return _error("Genderize returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    
    try:
        probability = float(probability)
        sample_size = int(sample_size)
    except (TypeError, ValueError):
        return _error("Genderize returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    
    return {
        "gender" : gender,
        "gender_probability" : probability,
        "sample_size" : sample_size
    }

def agify(name):
    try:
        api_response = requests.get(
            "https://api.agify.io/",    
            params={"name": name},
            timeout=10,
        )
        api_response.raise_for_status()
        data = api_response.json()
    except requests.Timeout:
        return _error("Agify API request timed out", status.HTTP_502_BAD_GATEWAY)
    except requests.RequestException:
        return _error("Failed to reach Agify API", status.HTTP_502_BAD_GATEWAY)
    except ValueError:
        return _error("Agify returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    
    age = data.get("age")

    if age is None:
        return _error("Agify returned an invalid response", status.HTTP_502_BAD_GATEWAY)

    try:
        age = int(age)
    except (TypeError, ValueError):
        return _error("Agify returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    age_group = ""
    if age >= 60:
        age_group = "senior"
    elif age >= 20 and age < 60:
        age_group = "adult"
    elif age >= 13 and age < 19:
        age_group = "teenager"
    else:
        age_group = "child"

    return {
        "age" : age,
        "age_group" : age_group
    }


def nationalize(name):
    try:
        api_response = requests.get(
            "https://api.nationalize.io/",    
            params={"name": name},
            timeout=10,
        )
        api_response.raise_for_status()
        data = api_response.json()
    except requests.Timeout:
        return _error("Nationalize API request timed out", status.HTTP_502_BAD_GATEWAY)
    except requests.RequestException:
        return _error("Failed to reach Nationalize API", status.HTTP_502_BAD_GATEWAY)
    except ValueError:
        return _error("Nationalize returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    
    country_list = data.get('country')

    if len(country_list) < 0:
        return _error("Nationalize returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    
    max_probability = 0
    print(max_probability)
    country = None
    for i in country_list:
        if i['probability'] > max_probability:
            max_probability = i['probability']
            country = i
    return {
        "country_id" : country["country_id"],
        "country_probability" : country["probability"]
    }


class ProfileCreateView(APIView):
    serializer_class = ProfileSerializer
    queryset = Profile

    def post(self, request, *args, **kwargs):
        serializer = ProfileSerializer(data=request.data)

        if not serializer.is_valid():
            return _error(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        name = serializer.validated_data['name']
        if name is None or name.strip() == "":
            return _error("'name' cannot be empty", status.HTTP_400_BAD_REQUEST)

        name = name.strip()

        genderize_response = genderize(name)
        agify_response = agify(name)
        nationalize_response = nationalize(name)

        serializer.save(**genderize_response, **agify_response, **nationalize_response)

        return Response({
            "status":"success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
