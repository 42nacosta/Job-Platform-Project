"""
Management command to geocode all jobs that don't have coordinates.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from home.models import Job
import requests
import time


class Command(BaseCommand):
    help = 'Geocode all jobs that do not have latitude/longitude coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be geocoded without making changes',
        )

    def geocode_location(self, address):
        """Geocode an address using Google Maps API."""
        if not address:
            return None, None

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": settings.GOOGLE_MAPS_API_KEY}

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data["status"] == "OK":
                loc = data["results"][0]["geometry"]["location"]
                return float(loc["lat"]), float(loc["lng"])
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'    Geocoding failed for "{address}": {data["status"]} - {data.get("error_message", "")}'
                    )
                )
                return None, None
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'    Error geocoding "{address}": {str(e)}')
            )
            return None, None

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find jobs without coordinates
        jobs_to_geocode = Job.objects.filter(latitude__isnull=True) | Job.objects.filter(longitude__isnull=True)
        total_jobs = jobs_to_geocode.count()

        if total_jobs == 0:
            self.stdout.write(self.style.SUCCESS('All jobs already have coordinates!'))
            return

        self.stdout.write(f'Found {total_jobs} jobs without coordinates')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No changes will be made\n'))

        geocoded_count = 0
        failed_count = 0
        skipped_count = 0

        for i, job in enumerate(jobs_to_geocode, 1):
            self.stdout.write(f'\n[{i}/{total_jobs}] Processing: "{job.title}" at "{job.location}"')
            
            if not job.location or job.location.lower() == 'remote':
                self.stdout.write(self.style.WARNING(f'    Skipping (Remote or no location)'))
                skipped_count += 1
                continue

            lat, lng = self.geocode_location(job.location)
            
            if lat is not None and lng is not None:
                self.stdout.write(
                    self.style.SUCCESS(f'    ✓ Geocoded: {lat}, {lng}')
                )
                
                if not dry_run:
                    job.latitude = lat
                    job.longitude = lng
                    job.save(update_fields=['latitude', 'longitude'])
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Saved to database'))
                
                geocoded_count += 1
                
                # Rate limiting: sleep to avoid hitting API limits
                if i < total_jobs:
                    time.sleep(0.2)  # 5 requests per second max
            else:
                failed_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('GEOCODING SUMMARY'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'Total jobs processed: {total_jobs}')
        self.stdout.write(self.style.SUCCESS(f'Successfully geocoded: {geocoded_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f'Failed to geocode: {failed_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped (remote/no location): {skipped_count}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nℹ️  This was a dry run. Run without --dry-run to save changes.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ All changes saved to database!'))
