import csv
import io
import uuid

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from api.models import ProjectOwnerCompany as Company, Person, User, UserRole
import json

class Command(BaseCommand):
    help = 'Import users into database from json file'
    companies = {}

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='path to json file')

    def handle(self, *args, **options):
        fname = options['json_file']
        with open(fname) as f:
            data = json.load(f)
        for d in data:
            p = Person(
                fullname=d['FISH'],
                phone=d['Telefon'],
            )
            if d['Tashkilot'] in self.companies:
                self.companies[d['Tashkilot']].append(p)
            else:
                self.companies[d['Tashkilot']] = [p]

        for c in self.companies:

            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # Write CSV header row
            writer.writerow(['Ismi', 'Familiyasi', 'Tizimdagi login', 'Kalit so\'z'])

            # 2. Build the users list in memory first (extremely fast)
            users_to_create = []
            csv_rows = []

            for p in self.companies[c]:
                unique_id = uuid.uuid4().hex[:8]
                username = f"user_{unique_id}"
                email = f"{username}@muallifnazorat.uz"
                first_name = p.fullname.split(" ")[1]
                last_name = p.fullname.split(" ")[0]

                # Instantiate User objects without saving to database yet
                user_obj = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=UserRole.SUPERVISOR,
                )
                p.profile = user_obj
                # Set standard unusable or dummy encrypted password
                password = get_random_string(14)
                user_obj.set_password(password)

                users_to_create.append(user_obj)
                csv_rows.append([first_name, last_name, username, password])

            # 3. Save ALL users to the database in a SINGLE database query
            User.objects.bulk_create(users_to_create)
            persons = Person.objects.bulk_create(self.companies[c])

            try:
                company = Company.objects.get(name=c)
            except Company.DoesNotExist:
                company = Company.objects.create(name=c, director=persons[0], contact_person=persons[0])
                self.stdout.write(f"Created company {company.id}, {company.name}")

            company.personal.add(*persons)

            # 4. Write all rows to the CSV buffer
            writer.writerows(csv_rows)
            with open(f"{c}.csv", "w", newline="", encoding="utf-8") as output:
                output.write(buffer.getvalue())


            print(c)
            print(self.companies[c])

        self.stdout.write(f"Found {len(data)} entries in the database.")