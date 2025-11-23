from collections import OrderedDict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Job, CandidateRecommendation, JobRecommendation, Application
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from accounts.models import Profile
from .recommendations import generate_candidate_recommendations, generate_job_recommendations
from django.db import models
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.db.models import Prefetch
from django.conf import settings
from home.forms import SavedCandidateSearchForm
from home.models import SavedCandidateSearch, SavedCandidateMatch
from home.services.saved_searches import run_search_and_record_new_matches
import math

import requests

# Create your views here.
def index(request):
    search_term = request.GET.get('search')
    search_type = request.GET.get('search_type')
    min_salary = request.GET.get('min_salary')
    max_salary = request.GET.get('max_salary')

    jobs = Job.objects.all()
    app = Application.objects.all()

    if search_term:
        if search_type in {'title', 'location', 'category'}:
            lookup = {f"{search_type}__icontains": search_term}
        else:
            lookup = {"title__icontains": search_term}
        jobs = jobs.filter(**lookup)
    if min_salary:
        jobs = jobs.filter(salary__gte=min_salary)
    if max_salary:
        jobs = jobs.filter(salary__lte=max_salary)

    template_data = {
        'title': 'Jobs',
        'jobs': jobs,
        'search_term': search_term or '',
        'search_type': search_type or 'title',
        'min_salary': min_salary or '',
        'max_salary': max_salary or '',
        'applications': app
    }
    return render(request, 'home/index.html', {'template_data': template_data})

def about(request):
    return render(request, 'home/about.html')

@login_required
def apps(request):
    template_data = {}
    template_data['applications'] = Application.objects.all()
    
    return render(request, 'home/apps.html', {'template_data': template_data})

def show(request, id):
    job = Job.objects.get(id=id)
    template_data = {}
    template_data['title'] = job.title
    template_data['job'] = job

    # PSEUDOCODE: surface applications only to job owner while keeping others unaware.
    if request.user.is_authenticated and request.user == job.user:
        template_data['applications'] = job.applications.select_related('applicant').all()
    else:
        template_data['applications'] = None

    return render(request, 'home/show.html', {'template_data': template_data})

@login_required
def create_job(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        salary_str = request.POST.get("salary", "0").strip()
        category = request.POST.get('category', '').strip()

        # Convert salary to number safely
        try:
            salary = int(Decimal(salary_str))
        except (TypeError, ValueError):
            salary = 0

        # Get latitude/longitude safely
        lat, lng = geocode_location(location)
        if lat is not None:
            lat = float(lat)
        if lng is not None:
            lng = float(lng)

        job = Job.objects.create(
            user=request.user,
            title=title,
            description=description,
            location=location,
            salary=salary,
            category=category,
            latitude=lat,
            longitude=lng
        )

        # Optional: generate candidate recommendations
        generate_candidate_recommendations(job.id)

        return redirect('home.show', id=job.id)

    return render(request, 'home/job_form.html', {
        'template_data': {'title': 'Post Job'},
        'job': None
    })

@login_required
def edit_job(request, id):
    job = get_object_or_404(Job, id=id)

    if job.user != request.user:
        return render(request, 'home/forbidden.html', status=403)

    if request.method == 'POST':
        new_title = request.POST.get('title', '').strip()
        new_description = request.POST.get('description', '').strip()
        new_location = request.POST.get('location', '').strip()
        new_salary_str = request.POST.get("salary", "0").strip()
        new_category = request.POST.get('category', '').strip()

        # Convert salary safely
        try:
            new_salary = int(Decimal(new_salary_str))
        except (TypeError, ValueError):
            new_salary = 0

        # Update latitude/longitude if location changed
        if new_location != job.location:
            lat, lng = geocode_location(new_location)
            if lat is not None:
                job.latitude = float(lat)
            if lng is not None:
                job.longitude = float(lng)

        # Update fields
        job.title = new_title
        job.description = new_description
        job.location = new_location
        job.salary = new_salary
        job.category = new_category

        job.save()
        generate_candidate_recommendations(job.id)

        return redirect('home.show', id=job.id)

    return render(request, 'home/job_form.html', {
        'template_data': {'title': 'Edit Job'},
        'job': job
    })

@login_required
@require_POST
def apply_job(request, id):
    job = get_object_or_404(Job, id=id)
    note = (request.POST.get("note") or "").strip()[:500]

    # Enforce single application per user per job; update note if already exists.
    from .models import Application
    app, created = Application.objects.get_or_create(
        job=job, applicant=request.user, defaults={"note": note}
    )
    if not created:
        app.note = note
        app.status = Application.Status.SUBMITTED
        app.save(update_fields=["note", "status", "updated_at"])
        messages.success(request, "Application updated.")
    else:
        messages.success(request, "Application submitted.")

    # PSEUDOCODE: Remove candidate from job recommendations after applying
    # Prevents recommending jobs/candidates where application already exists
    CandidateRecommendation.objects.filter(job=job, candidate=request.user).delete()
    JobRecommendation.objects.filter(candidate=request.user, job=job).delete()

    return redirect("home.show", id=job.id)

@login_required
def candidates(request):
    # Only recruiters can view
    if not request.user.profile.is_recruiter:
        return render(request, 'home/forbidden.html', status=403)

    profiles = (
        Profile.objects
        .select_related("user")
        .filter(
            is_recruiter=False,
            user__is_active=True,
            user__is_staff=False,
            user__is_superuser=False,
        )
        .exclude(user=request.user)
    )

    # Get recruiter's jobs for filter
    recruiter_jobs = Job.objects.filter(user=request.user).order_by('-date')

    # Searches
    search_skills = (request.GET.get("skills") or "").strip()
    search_location = (request.GET.get("location") or "").strip()
    search_name = (request.GET.get("name") or "").strip()
    filter_job_id = request.GET.get("job")

    if search_skills:
        profiles = profiles.filter(skills__icontains=search_skills)
    if search_location:
        profiles = profiles.filter(location__icontains=search_location)
    if search_name:
        profiles = profiles.filter(
            models.Q(firstName__icontains=search_name) |
            models.Q(lastName__icontains=search_name) |
            models.Q(user__username__icontains=search_name)
        )

    # Filter by job applicants
    filtered_by_job = None
    if filter_job_id:
        try:
            job = Job.objects.get(id=filter_job_id, user=request.user)
            filtered_by_job = job
            applicant_ids = job.applications.values_list('applicant_id', flat=True)
            profiles = profiles.filter(user_id__in=applicant_ids)
        except Job.DoesNotExist:
            pass

    safe_profiles = []
    for profile in profiles:
        if getattr(Profile, "Visibility", None) and profile.visibility == Profile.Visibility.PRIVATE:
            continue

        # Skip if no meaningful data to show
        has_data = any([
            getattr(profile, "show_firstName_to_recruiters", False) and profile.firstName,
            getattr(profile, "show_lastName_to_recruiters", False) and profile.lastName,
            getattr(profile, "show_skills_to_recruiters", False) and profile.skills,
            getattr(profile, "show_location_to_recruiters", False) and profile.location,
            getattr(profile, "show_experience_to_recruiters", False) and profile.experience,
        ])

        if not has_data:
            continue

        safe_profiles.append({
            "firstName": profile.firstName if getattr(profile, "show_firstName_to_recruiters", False) else None,
            "lastName": profile.lastName if getattr(profile, "show_lastName_to_recruiters", False) else None,
            "email": profile.email if getattr(profile, "show_email_to_recruiters", False) else None,
            "phone": profile.phone if getattr(profile, "show_phone_to_recruiters", False) else None,
            "location": profile.location if getattr(profile, "show_location_to_recruiters", False) else None,
            "skills": profile.skills if getattr(profile, "show_skills_to_recruiters", False) else None,
            "projects": profile.projects if getattr(profile, "show_projects_to_recruiters", False) else None,
            "education": profile.education if getattr(profile, "show_education_to_recruiters", False) else None,
            "experience": profile.experience if getattr(profile, "show_experience_to_recruiters", False) else None,
            "resume_url": profile.resume_url if getattr(profile, "show_resume_to_recruiters", False) else None,
            "username": (profile.user.username if profile.user and profile.user.username else None),
        })

    context = {
        "profiles": safe_profiles,
        "search_skills": search_skills,
        "search_location": search_location,
        "search_name": search_name,
        "recruiter_jobs": recruiter_jobs,
        "filter_job_id": filter_job_id,
        "filtered_by_job": filtered_by_job,
    }
    return render(request, "home/candidates.html", context)


# PSEUDOCODE: View showing recommended candidates for a specific job (recruiter-only)
# Fetches CandidateRecommendation records for the job, filters by score threshold
# Interacts with: CandidateRecommendation model, Profile model for candidate data
@login_required
def recruiter_recommendations(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Only job owner can view recommendations
    if job.user != request.user:
        return render(request, 'home/forbidden.html', status=403)

    # Get min score filter (default: 10)
    min_score = int(request.GET.get('min_score', 10))

    # Fetch recommendations, exclude dismissed ones
    recommendations = (
        CandidateRecommendation.objects
        .filter(job=job, is_dismissed=False, match_score__gte=min_score)
        .select_related('candidate__profile')
        .order_by('-match_score', '-created_at')
    )

    # Build safe candidate data respecting privacy settings
    safe_recommendations = []
    for rec in recommendations:
        profile = rec.candidate.profile
        if profile.visibility == Profile.Visibility.PRIVATE:
            continue

        safe_recommendations.append({
            'id': rec.id,
            'username': rec.candidate.username,
            'match_score': rec.match_score,
            'firstName': profile.firstName if profile.show_firstName_to_recruiters else None,
            'lastName': profile.lastName if profile.show_lastName_to_recruiters else None,
            'location': profile.location if profile.show_location_to_recruiters else None,
            'skills': profile.skills if profile.show_skills_to_recruiters else None,
            'experience': profile.experience if profile.show_experience_to_recruiters else None,
        })

    context = {
        'job': job,
        'recommendations': safe_recommendations,
        'min_score': min_score,
    }
    return render(request, 'home/recruiter_recommendations.html', context)


# PSEUDOCODE: Dismisses a candidate recommendation (recruiter action)
# Marks CandidateRecommendation as dismissed, preventing it from appearing in lists
# Interacts with: CandidateRecommendation model
@login_required
@require_POST
def dismiss_candidate_recommendation(request, rec_id):
    rec = get_object_or_404(CandidateRecommendation, id=rec_id)

    # Only job owner can dismiss
    if rec.job.user != request.user:
        return render(request, 'home/forbidden.html', status=403)

    rec.is_dismissed = True
    rec.save(update_fields=['is_dismissed'])
    messages.success(request, "Candidate recommendation dismissed.")

    return redirect('home.recruiter_recs', job_id=rec.job.id)


# PSEUDOCODE: View showing recommended jobs for job seeker based on their profile
# Fetches JobRecommendation records for the user, excludes dismissed/applied jobs
# Interacts with: JobRecommendation model, Job model for posting data
@login_required
def job_recommendations(request):
    # Get min score filter (default: 10)
    min_score = int(request.GET.get('min_score', 10))

    # Fetch recommendations, exclude dismissed ones
    recommendations = (
        JobRecommendation.objects
        .filter(candidate=request.user, is_dismissed=False, match_score__gte=min_score)
        .select_related('job__user')
        .order_by('-match_score', '-created_at')
    )

    context = {
        'recommendations': recommendations,
        'min_score': min_score,
    }
    return render(request, 'home/job_recommendations.html', context)


# PSEUDOCODE: Dismisses a job recommendation (job seeker action)
# Marks JobRecommendation as dismissed, preventing it from appearing in lists
# Interacts with: JobRecommendation model
@login_required
@require_POST
def dismiss_job_recommendation(request, rec_id):
    rec = get_object_or_404(JobRecommendation, id=rec_id)

    # Only the candidate can dismiss their own recommendations
    if rec.candidate != request.user:
        return render(request, 'home/forbidden.html', status=403)

    rec.is_dismissed = True
    rec.save(update_fields=['is_dismissed'])
    messages.success(request, "Job recommendation dismissed.")

    return redirect('home.job_recs')

@login_required
def move_app(request, id):
    print("\n--- move_app called ---")
    print(f"Request method: {request.method}, User: {request.user}")

    if request.method != "POST":
        print("Not a POST request!")
        messages.error(request, "Invalid request method.")
        return redirect('home:show', id=id)

    app = get_object_or_404(Application, id=id)
    print(f"Application found: id={app.id}, current status='{app.status}'")

    # Authorization check: only the job owner can move application
    if request.user != app.job.user:
        print(f"User not authorized: app.job.user={app.job.user}")
        messages.error(request, "Not authorized.")
        return redirect('home:show', id=app.job.id)

    # Define allowed transitions
    transitions = {
        app.Status.SUBMITTED: app.Status.REVIEW,
        app.Status.REVIEW: app.Status.INTERVIEW,
        app.Status.INTERVIEW: app.Status.OFFER,
    }

    new_status = transitions.get(app.status)
    print(f"New status determined: {new_status}")

    if new_status:
        app.status = new_status
        app.save()
        print(f"Application status updated to: {app.status}")
        messages.success(request, f"Application moved to {app.status}.")
    else:
        print("No valid transition found; status not updated.")
        messages.info(request, "Cannot move application further.")

    print("--- move_app finished ---\n")
    return redirect('home.show', id=app.job.id)

PIPELINE_COLUMNS = [
    ("SUBMITTED",  "Submitted"),
    ("SCREENING",  "Screening"),
    ("INTERVIEW",  "Interview"),
    ("OFFER",      "Offer"),
    ("HIRED",      "Hired"),
    ("REJECTED",   "Rejected"),
    ("WITHDRAWN",  "Withdrawn"),
]

def _user_can_manage_job(user, job: Job|None):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if job is None:
        return user.is_staff
    return job.user_id == user.id

@login_required
def pipeline_board(request, job_id=None):
    job = None
    if job_id:
        job = get_object_or_404(Job.objects.select_related("user"), pk=job_id)
        if not _user_can_manage_job(request.user, job):
            return HttpResponseForbidden("You don't have access to this job.")

    qs = Application.objects.select_related("job", "applicant")
    if job:
        qs = qs.filter(job=job)
    elif not request.user.is_staff:
        qs = qs.filter(job__user=request.user)

    columns = []
    for value, label in PIPELINE_COLUMNS:
        items = [a for a in qs if a.status == value]
        columns.append({"value": value, "label": label, "items": items})

    ctx = {
        "columns": columns,
        "job": job,
        "pipeline_choices": PIPELINE_COLUMNS,
    }
    return render(request, "home/pipeline_board.html", ctx)

@login_required
def pipeline_update_status(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    app_id = request.POST.get("application_id")
    new_status = request.POST.get("new_status")

    if not app_id or not new_status:
        return JsonResponse({"ok": False, "error": "Missing parameters"}, status=400)

    app = get_object_or_404(Application.objects.select_related("job", "job__user"), pk=app_id)

    if not _user_can_manage_job(request.user, app.job):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    valid = dict(Application.Status.choices).keys()
    if new_status not in valid:
        return JsonResponse({"ok": False, "error": "Invalid status"}, status=400)

    app.status = new_status
    app.save(update_fields=["status"])
    return JsonResponse({"ok": True, "id": app.id, "status": app.status})

# Saved search implementation

def _must_be_recruiter(user):
    try:
        return user.is_authenticated and user.profile.is_recruiter
    except Exception:
        return False

@login_required
def saved_search_list(request):
    if not _must_be_recruiter(request.user):
        return HttpResponseForbidden("Recruiters only")
    searches = SavedCandidateSearch.objects.filter(owner=request.user).order_by("-updated_at")
    return render(request, "home/saved_search_list.html", {"searches": searches})

@login_required
def saved_search_create(request):
    if not _must_be_recruiter(request.user):
        return HttpResponseForbidden("Recruiters only")
    if request.method == "POST":
        form = SavedCandidateSearchForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.owner = request.user
            s.save()
            # initial run so the list isn't empty
            run_search_and_record_new_matches(s)
            return redirect("saved_search_list")
    else:
        # Optionally prefill from current query string on the candidates search page
        initial = {
            "keywords": request.GET.get("keywords", ""),
            "location": request.GET.get("location", ""),
            "min_years_experience": request.GET.get("min_years_experience", 0),
        }
        form = SavedCandidateSearchForm(initial=initial)
    return render(request, "home/saved_search_create.html", {"form": form})

@login_required
def saved_search_toggle(request, pk):
    if not _must_be_recruiter(request.user):
        return HttpResponseForbidden("Recruiters only")
    s = get_object_or_404(SavedCandidateSearch, pk=pk, owner=request.user)
    s.is_active = not s.is_active
    s.save(update_fields=["is_active"])
    return redirect("saved_search_list")

@login_required
def saved_search_matches(request, pk):
    if not _must_be_recruiter(request.user):
        return HttpResponseForbidden("Recruiters only")
    s = get_object_or_404(SavedCandidateSearch, pk=pk, owner=request.user)
    matches = (
        SavedCandidateMatch.objects
        .filter(search=s)
        .select_related("candidate", "candidate__profile")
        .order_by("-matched_at")
    )
    return render(request, "home/saved_search_matches.html", {"search": s, "matches": matches})

@login_required
def saved_search_unread_count(request):
    if not _must_be_recruiter(request.user):
        return JsonResponse({"count": 0})
    count = SavedCandidateMatch.objects.filter(search__owner=request.user, seen=False).count()
    return JsonResponse({"count": count})

@login_required
def saved_search_mark_seen(request):
    if not _must_be_recruiter(request.user):
        return JsonResponse({"ok": False})
    SavedCandidateMatch.objects.filter(search__owner=request.user, seen=False).update(seen=True)
    return JsonResponse({"ok": True})

# Location Map Page: Render map template with Google Maps API key for user
def job_map(request):
    template_data = {
        'title': 'Job Posts Map',
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'home/job_map.html', {'template_data': template_data})

# Location Map Page: API endpoint to filter and return job data based on location/distance
@login_required
def map_data_api(request):
    # Location Map Page: Calculate geographic distance between two points using Haversine formula
    def haversine(lat1, lon1, lat2, lon2):
        R = 3958.8  # Earth radius in miles
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    # Location Map Page: Parse user filters from request parameters
    max_distance = float(request.GET.get("distance") or math.inf)
    user_location = request.GET.get("location", None)

    # Location Map Page: Convert user's city to coordinates for distance filtering
    if user_location:
        user_lat, user_lng = geocode_location(user_location)
    else:
        # No location entered → distance filtering disabled
        user_lat, user_lng = None, None

    jobs_by_city = OrderedDict()

    # Location Map Page: Loop through jobs, filter by distance, group by city
    for job in Job.objects.order_by("location", "date"):
        # Must have coordinates (from the geocoding process at job creation)
        if job.latitude is None or job.longitude is None:
            continue

        lat, lng = job.latitude, job.longitude

        # Location Map Page: Apply distance filtering if user specified location
        if user_lat is not None and user_lng is not None:
            curr_distance = haversine(user_lat, user_lng, lat, lng)
            if curr_distance > max_distance:
                continue

        city = job.location  # Group jobs by the text location

        # Location Map Page: Group jobs by city for marker clustering
        if city not in jobs_by_city:
            jobs_by_city[city] = {
                "location": city,
                "lat": lat,
                "lng": lng,
                "jobs": []
            }

        # Location Map Page: Add job details to city's job list
        jobs_by_city[city]["jobs"].append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "salary": job.salary,
            "date": job.date.strftime("%b %d, %Y"),
            "category": job.category,
        })

    return JsonResponse(list(jobs_by_city.values()), safe=False)

# map clustering functions

@login_required
def applicant_map(request):
    if not request.user.profile.is_recruiter:
        return render(request, 'home/forbidden.html', status=403)
    
    recruiter_jobs = Job.objects.filter(user=request.user).order_by('-date')
    
    template_data = {
        'title': 'Applicant Location Map',
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'recruiter_jobs': recruiter_jobs
    }
    return render(request, 'home/applicant_map.html', {'template_data': template_data})

@login_required
def applicant_map_data_api(request):
    if not request.user.profile.is_recruiter:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    job_id = request.GET.get('job_id')
    
    applicant_locations = OrderedDict()
    
    coords = {
        # Major Metropolitan Areas
        "New York City, NY": (40.7128, -74.0060),
        "Los Angeles, CA": (34.0522, -118.2437),
        "Chicago, IL": (41.8781, -87.6298),
        "Houston, TX": (29.7604, -95.3698),
        "Phoenix, AZ": (33.4484, -112.0740),
        "Philadelphia, PA": (39.9526, -75.1652),
        "San Antonio, TX": (29.4241, -98.4936),
        "San Diego, CA": (32.7157, -117.1611),
        "Dallas, TX": (32.7767, -96.7970),
        "San Jose, CA": (37.3382, -121.8863),
        
        # Tech Hubs
        "San Francisco, CA": (37.7749, -122.4194),
        "Seattle, WA": (47.6062, -122.3321),
        "Austin, TX": (30.2672, -97.7431),
        "Boston, MA": (42.3601, -71.0589),
        "Denver, CO": (39.7392, -104.9903),
        "Portland, OR": (45.5152, -122.6784),
        "Raleigh, NC": (35.7796, -78.6382),
        "Nashville, TN": (36.1627, -86.7816),
        
        # Southeast
        "Atlanta, GA": (33.7501, -84.3885),
        "Miami, FL": (25.7617, -80.1918),
        "Orlando, FL": (28.5383, -81.3792),
        "Tampa, FL": (27.9506, -82.4572),
        "Charlotte, NC": (35.2271, -80.8431),
        "Jacksonville, FL": (30.3322, -81.6557),
        "New Orleans, LA": (29.9511, -90.0715),
        "Birmingham, AL": (33.5186, -86.8104),
        
        # Midwest
        "Detroit, MI": (42.3314, -83.0458),
        "Minneapolis, MN": (44.9778, -93.2650),
        "Cleveland, OH": (41.4993, -81.6944),
        "Indianapolis, IN": (39.7684, -86.1581),
        "Columbus, OH": (39.9612, -82.9988),
        "Milwaukee, WI": (43.0389, -87.9065),
        "Kansas City, MO": (39.0997, -94.5786),
        "St. Louis, MO": (38.6270, -90.1994),
        "Cincinnati, OH": (39.1031, -84.5120),
        
        # Northeast
        "Washington, DC": (38.9072, -77.0369),
        "Baltimore, MD": (39.2904, -76.6122),
        "Pittsburgh, PA": (40.4406, -79.9959),
        "Buffalo, NY": (42.8864, -78.8784),
        "Hartford, CT": (41.7658, -72.6734),
        "Providence, RI": (41.8240, -71.4128),
        "Albany, NY": (42.6526, -73.7562),
        
        # West Coast
        "Sacramento, CA": (38.5816, -121.4944),
        "Oakland, CA": (37.8044, -122.2712),
        "Fresno, CA": (36.7378, -119.7871),
        "Las Vegas, NV": (36.1699, -115.1398),
        "Albuquerque, NM": (35.0844, -106.6504),
        "Salt Lake City, UT": (40.7608, -111.8910),
        "Boise, ID": (43.6150, -116.2023),
        
        # Mountain/Plains
        "Colorado Springs, CO": (38.8339, -104.8214),
        "Omaha, NE": (41.2565, -95.9345),
        "Oklahoma City, OK": (35.4676, -97.5164),
        "Tulsa, OK": (36.1540, -95.9928),
        "Wichita, KS": (37.6872, -97.3301),
        
        # Additional Major Cities
        "Richmond, VA": (37.5407, -77.4360),
        "Norfolk, VA": (36.9148, -76.2587),
        "Memphis, TN": (35.1495, -90.0490),
        "Louisville, KY": (38.2527, -85.7585),
        "Little Rock, AR": (34.7465, -92.2896),
        "Jackson, MS": (32.2988, -90.1848),
        "Mobile, AL": (30.6954, -88.0399),
        "Savannah, GA": (32.0835, -81.0998),
        
        # Common Variations/Abbreviations
        "NYC": (40.7128, -74.0060),
        "LA": (34.0522, -118.2437),
        "SF": (37.7749, -122.4194),
        "DC": (38.9072, -77.0369),
    }
    
    applications_query = Application.objects.filter(
        job__user=request.user
    ).select_related('applicant', 'applicant__profile', 'job')
    
    if job_id and job_id != 'all':
        try:
            job_id = int(job_id)
            applications_query = applications_query.filter(job_id=job_id)
        except (ValueError, TypeError):
            pass
    
    applications = applications_query
    
    for app in applications:
        profile = app.applicant.profile
        loc = profile.location if hasattr(profile, 'location') else None
        
        if not loc or loc not in coords:
            continue
            
        lat, lng = coords[loc]
        
        if loc not in applicant_locations:
            applicant_locations[loc] = {
                "location": loc,
                "lat": lat,
                "lng": lng,
                "applicants": [],
                "count": 0
            }
        
        applicant_locations[loc]['applicants'].append({
            "id": app.id,
            "job_title": app.job.title,
            "job_id": app.job.id,
            "applicant_name": f"{profile.firstName} {profile.lastName}" if hasattr(profile, 'firstName') and profile.firstName else app.applicant.username,
            "applied_date": app.created_at.strftime("%b %d, %Y"),
            "status": app.status
        })
        applicant_locations[loc]['count'] += 1
    
    return JsonResponse(list(applicant_locations.values()), safe=False)

# Location Map Page: Convert city/address to latitude/longitude using Google Geocoding API
def geocode_location(address):
    if not address:
        return None, None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": settings.GOOGLE_MAPS_API_KEY}

    response = requests.get(url, params=params).json()
    print("Geocoding response for", address, ":", response)  # <-- add this

    if response["status"] == "OK":
        loc = response["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    else:
        print("Geocoding failed:", response["status"], response.get("error_message"))
        return None, None