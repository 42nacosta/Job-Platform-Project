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
from home.forms import SavedCandidateSearchForm
from home.models import SavedCandidateSearch, SavedCandidateMatch
from home.services.saved_searches import run_search_and_record_new_matches

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
        salary = Decimal(request.POST.get("salary")) or 0
        category = request.POST.get('category', '').strip()

        job = Job.objects.create(user=request.user, title=title, description=description,
            location=location, salary=int(salary), category=category)

        # PSEUDOCODE: After job creation, generate candidate recommendations for this job
        # Calls recommendation engine to find matching candidates based on skills/location
        generate_candidate_recommendations(job.id)

        return redirect('home.show', id=job.id)
    return render(request, 'home/job_form.html', {'template_data': {'title': 'Post Job'}, 'job': None})

@login_required
def edit_job(request, id):
    job = get_object_or_404(Job, id=id)
    if job.user != request.user:
        return render(request, 'home/forbidden.html', status=403)
    if request.method == 'POST':
        job.title = request.POST.get('title','').strip()
        job.description = request.POST.get('description','').strip()
        job.location = request.POST.get('location','').strip()
        job.salary = Decimal(request.POST.get("salary")) or 0
        job.category = request.POST.get('category','').strip()
        job.save()
        return redirect('home.show', id=job.id)
    return render(request, 'home/job_form.html', {'template_data': {'title': 'Edit Job'}, 'job': job})


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

    # Get min score filter (default: 20)
    min_score = int(request.GET.get('min_score', 20))

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
    # Get min score filter (default: 20)
    min_score = int(request.GET.get('min_score', 20))

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
