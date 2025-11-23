#!/usr/bin/env python
"""Check jobs database for geocoding status."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobplatform.settings')
django.setup()

from home.models import Job

jobs = Job.objects.all()
print(f'Total jobs: {jobs.count()}')

jobs_with_coords = jobs.filter(latitude__isnull=False, longitude__isnull=False)
print(f'Jobs with coordinates: {jobs_with_coords.count()}')

jobs_without_coords = jobs.filter(latitude__isnull=True) | jobs.filter(longitude__isnull=True)
print(f'Jobs WITHOUT coordinates: {jobs_without_coords.count()}')

print('\nSample jobs:')
for job in jobs[:5]:
    print(f'  - ID {job.id}: "{job.title}" at {job.location}')
    print(f'    Coordinates: lat={job.latitude}, lng={job.longitude}')
