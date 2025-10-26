# PSEUDOCODE: Recommendation engine for matching jobs to candidates and vice versa
# Core matching uses skill tokenization (simple word matching) + location comparison
# Interacts with: Job, Profile, CandidateRecommendation, JobRecommendation models

from django.db.models import Q
from .models import Job, CandidateRecommendation, JobRecommendation
from accounts.models import Profile


# PSEUDOCODE: Improved skill matching using multiple signals
# Analyzes profile skills/experience/education against job requirements
# Returns 0-100 match score with emphasis on relevant keyword overlap
def calculate_skill_match(profile_skills, job_description):
    """
    Calculate skill match score between profile and job.
    Uses multiple scoring methods and takes the best result.
    Returns integer 0-100 representing percentage match.
    """
    if not profile_skills or not job_description:
        return 0

    # Normalize and tokenize
    profile_text = profile_skills.lower().replace(',', ' ').replace(';', ' ').replace('-', ' ')
    job_text = job_description.lower().replace(',', ' ').replace(';', ' ').replace('-', ' ')
    
    profile_tokens = set(profile_text.split())
    job_tokens = set(job_text.split())

    # Expanded stop words list - common words that don't indicate skills/fit
    stop_words = {
        'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'we', 'are', 'is', 'you', 'will', 'be', 'our', 'your', 'this', 'that', 'as', 'it',
        'from', 'has', 'have', 'can', 'all', 'about', 'their', 'use', 'work', 'also', 'who',
        'but', 'not', 'they', 'which', 'been', 'were', 'would', 'should', 'could', 'may',
        'into', 'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down',
        'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
        'when', 'where', 'why', 'how', 'than', 'too', 'very', 'such', 'these', 'those'
    }
    
    profile_tokens = profile_tokens - stop_words
    job_tokens = job_tokens - stop_words

    if not profile_tokens or not job_tokens:
        return 0

    # Calculate matching tokens
    matching_tokens = profile_tokens & job_tokens
    match_count = len(matching_tokens)
    
    # METHOD 1: Keyword density approach
    # Focus on what percentage of meaningful job keywords the candidate has
    keyword_score = (match_count / len(job_tokens)) * 100 if job_tokens else 0
    
    # METHOD 2: Candidate relevance approach  
    # What percentage of candidate's skills are relevant to this job
    relevance_score = (match_count / len(profile_tokens)) * 100 if profile_tokens else 0
    
    # METHOD 3: Balanced Jaccard-like approach
    # Overall overlap considering both sides
    union_size = len(profile_tokens | job_tokens)
    jaccard_score = (match_count / union_size) * 100 if union_size else 0
    
    # Boost score if there are many matching keywords (shows strong fit)
    match_bonus = min(match_count * 3, 30)  # Up to 30 point bonus for lots of matches
    
    # Take weighted combination favoring keyword coverage
    # This makes candidates with relevant skills score higher
    base_score = (keyword_score * 0.5 + relevance_score * 0.3 + jaccard_score * 0.2)
    final_score = min(base_score + match_bonus, 100)
    
    return int(final_score)


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

        # Build comprehensive profile text from multiple fields
        profile_text_parts = []
        if profile.skills:
            profile_text_parts.append(profile.skills)
        if profile.experience:
            profile_text_parts.append(profile.experience)
        if profile.education:
            profile_text_parts.append(profile.education)
        
        profile_text = " ".join(profile_text_parts)
        
        # Calculate match scores
        skill_score = calculate_skill_match(
            profile_text,
            job.description + " " + job.title + " " + job.category
        )
        location_score = calculate_location_match(profile.location or "", job.location)

        # Weighted composite score: 75% skills/experience/education, 25% location
        composite_score = int((skill_score * 0.75) + (location_score * 0.25))

        # Lower threshold to show more opportunities (was 15)
        if composite_score > 10:
            recommendations.append({
                'candidate': profile.user,
                'score': composite_score
            })

    # Sort by score and take top 15 (increased from 10)
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = recommendations[:15]

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

    # Build comprehensive profile text from multiple fields
    profile_text_parts = []
    if profile.skills:
        profile_text_parts.append(profile.skills)
    if profile.experience:
        profile_text_parts.append(profile.experience)
    if profile.education:
        profile_text_parts.append(profile.education)
    
    profile_text = " ".join(profile_text_parts)

    for job in jobs:
        # Calculate match scores
        skill_score = calculate_skill_match(
            profile_text,
            job.description + " " + job.title + " " + job.category
        )
        location_score = calculate_location_match(profile.location or "", job.location)

        # Weighted composite score: 75% skills/experience/education, 25% location
        composite_score = int((skill_score * 0.75) + (location_score * 0.25))

        # Lower threshold to show more opportunities (was 15)
        if composite_score > 10:
            recommendations.append({
                'job': job,
                'score': composite_score
            })

    # Sort by score and take top 15 (increased from 10)
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = recommendations[:15]

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
