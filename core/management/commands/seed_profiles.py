import json
from django.core.management.base import BaseCommand
from core.models import Profile  # Update this with your app/model name

class Command(BaseCommand):
    help = 'Seeds profile data from a specific JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        file_path = options['json_file']
        
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                profiles = data.get('profiles', [])
                print(len(profiles))

                for item in profiles:
                    # update_or_create prevents duplicate entries
                    Profile.objects.update_or_create(
                        name=item['name'],
                        defaults={
                            'gender': item['gender'],
                            'gender_probability': item['gender_probability'],
                            'age': item['age'],
                            'age_group': item['age_group'],
                            'country_id': item['country_id'],
                            'country_name': item['country_name'],
                            'country_probability': item['country_probability'],
                        }
                    )
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(profiles)} profiles'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
