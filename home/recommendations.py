# PSEUDOCODE: Recommendation engine for matching jobs to candidates and vice versa
# Core matching uses skill tokenization (simple word matching) + location comparison
# Interacts with: Job, Profile, CandidateRecommendation, JobRecommendation models

from django.db.models import Q
from .models import Job, CandidateRecommendation, JobRecommendation
from accounts.models import Profile


# PSEUDOCODE: Tokenizes and compares skill strings using Jaccard similarity
# Takes two skill text strings, lowercases, splits by common delimiters
# Returns 0-100 match score based on set intersection/union
def calculate_skill_match(profile_skills, job_description):
    """
    Calculate skill match score between profile and job.
    Returns integer 0-100 representing percentage match.
    """
    if not profile_skills or not job_description:
        return 0

    # Normalize and tokenize
    profile_tokens = set(profile_skills.lower().replace(',', ' ').replace(';', ' ').split())
    job_tokens = set(job_description.lower().replace(',', ' ').replace(';', ' ').split())

    # Remove common words that don't indicate skills
    stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    profile_tokens = profile_tokens - stop_words
    job_tokens = job_tokens - stop_words

    if not profile_tokens or not job_tokens:
        return 0

    # Jaccard similarity: intersection / union
    intersection = len(profile_tokens & job_tokens)
    union = len(profile_tokens | job_tokens)

    if union == 0:
        return 0

    return int((intersection / union) * 100)


# PSEUDOCODE: Compares location strings with exact/partial/no match scoring
# Returns 100 for exact match, 50 for partial (substring), 0 for no match
def calculate_location_match(profile_location, job_location):
    """
    Calculate location match score.
    Returns 100 for exact match, 50 for partial, 0 for no match.
    """
    if not profile_location or not job_location:
        return 0

    profile_loc = profile_location.lower().strip()
    job_loc = job_location.lower().strip()

    if profile_loc == job_loc:
        return 100
    elif profile_loc in job_loc or job_loc in profile_loc:
        return 50
    else:
        return 0


# PSEUDOCODE: Finds top candidates for a job posting based on skills/location
# Filters profiles by recruiter visibility settings, calculates composite match score
# Creates/updates CandidateRecommendation records for top 10 matches (score > 20)
def generate_candidate_recommendations(job_id):
    """
    Generate candidate recommendations for a specific job.
    Finds candidates matching job requirements, respecting privacy settings.
    Creates CandidateRecommendation records for top matches.
    """
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return

    # Get all candidate profiles that are visible to recruiters
    candidates = Profile.objects.select_related('user').filter(
        is_recruiter=False,
        user__is_active=True,
        user__is_staff=False,
        user__is_superuser=False
    ).exclude(
        visibility=Profile.Visibility.PRIVATE
    ).exclude(
        user=job.user  # Don't recommend job poster themselves
    )

    recommendations = []

    for profile in candidates:
        # Skip if they've already applied
        if job.applications.filter(applicant=profile.user).exists():
            continue

        # Calculate match scores
        skill_score = calculate_skill_match(
            profile.skills or "",
            job.description + " " + job.title + " " + job.category
        )
        location_score = calculate_location_match(profile.location or "", job.location)

        # Weighted composite score: 60% skills, 40% location
        composite_score = int((skill_score * 0.6) + (location_score * 0.4))

        # Only save recommendations with meaningful match scores
        if composite_score > 20:
            recommendations.append({
                'candidate': profile.user,
                'score': composite_score
            })

    # Sort by score and take top 10
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = recommendations[:10]

    # Create or update recommendation records
    for rec in top_recommendations:
        CandidateRecommendation.objects.update_or_create(
            job=job,
            candidate=rec['candidate'],
            defaults={
                'match_score': rec['score'],
                'is_dismissed': False  # Reset dismissal on update
            }
        )


# PSEUDOCODE: Finds top jobs for a candidate based on their profile skills/location
# Filters active jobs, calculates composite match score using weighted algorithm
# Creates/updates JobRecommendation records for top 10 matches (score > 20)
def generate_job_recommendations(user):
    """
    Generate job recommendations for a specific candidate.
    Finds jobs matching candidate's skills and location.
    Creates JobRecommendation records for top matches.
    """
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return

    # Don't generate recommendations for recruiters
    if profile.is_recruiter:
        return

    # Get all active jobs (exclude jobs the user already applied to)
    jobs = Job.objects.select_related('user').exclude(
        applications__applicant=user
    ).exclude(
        user=user  # Don't recommend their own jobs
    )

    recommendations = []

    for job in jobs:
        # Calculate match scores
        skill_score = calculate_skill_match(
            profile.skills or "",
            job.description + " " + job.title + " " + job.category
        )
        location_score = calculate_location_match(profile.location or "", job.location)

        # Weighted composite score: 60% skills, 40% location
        composite_score = int((skill_score * 0.6) + (location_score * 0.4))

        # Only save recommendations with meaningful match scores
        if composite_score > 20:
            recommendations.append({
                'job': job,
                'score': composite_score
            })

    # Sort by score and take top 10
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = recommendations[:10]

    # Create or update recommendation records
    for rec in top_recommendations:
        JobRecommendation.objects.update_or_create(
            candidate=user,
            job=rec['job'],
            defaults={
                'match_score': rec['score'],
                'is_dismissed': False  # Reset dismissal on update
            }
        )


# PSEUDOCODE: Triggers recommendation generation for user's context
# For recruiters: regenerates candidate recommendations for all their jobs
# For job seekers: regenerates job recommendations based on their profile
def refresh_recommendations(user):
    """
    Refresh all recommendations for a user.
    For recruiters: refresh candidate recommendations for all their jobs.
    For job seekers: refresh job recommendations based on their profile.
    """
    try:
        profile = user.profile

        if profile.is_recruiter:
            # Refresh candidate recommendations for all recruiter's jobs
            user_jobs = Job.objects.filter(user=user)
            for job in user_jobs:
                generate_candidate_recommendations(job.id)
        else:
            # Refresh job recommendations for candidate
            generate_job_recommendations(user)
    except Profile.DoesNotExist:
        pass
