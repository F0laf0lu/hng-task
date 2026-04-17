from rest_framework import serializers
from core.models import Profile




# name is the only thing provided in by theuser. Every other thing is gotten fro mthe apis and inserted.
# So all fields need to be read only except the name field.

class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(ProfileSerializer, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'name':
                self.fields[field].read_only = True




