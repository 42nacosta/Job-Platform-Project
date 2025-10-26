from django.core.management.base import BaseCommand
from home.recommendations import generate_job_recommendations, generate_candidate_recommendations
from home.models import Job, JobRecommendation, CandidateRecommendation
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Refresh all job and candidate recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing recommendations before regenerating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing recommendations...')
            JobRecommendation.objects.all().delete()
            CandidateRecommendation.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared'))

        self.stdout.write('Generating job recommendations for candidates...')
        candidates = Profile.objects.filter(is_recruiter=False)
        job_rec_count = 0
        for profile in candidates:
            if profile.skills and profile.location:
                generate_job_recommendations(profile.user)
                count = JobRecommendation.objects.filter(candidate=profile.user).count()
                if count > 0:
                    job_rec_count += count
                    self.stdout.write(f'  ✓ {profile.user.username}: {count} recommendations')

        self.stdout.write('\nGenerating candidate recommendations for jobs...')
        jobs = Job.objects.all()
        candidate_rec_count = 0
        for job in jobs:
            generate_candidate_recommendations(job.id)
            count = CandidateRecommendation.objects.filter(job=job).count()
            if count > 0:
                candidate_rec_count += count
                self.stdout.write(f'  ✓ {job.title}: {count} recommendations')

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Generated {job_rec_count} job recommendations and {candidate_rec_count} candidate recommendations'
        ))
