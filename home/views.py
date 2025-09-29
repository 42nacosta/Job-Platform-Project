from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Job
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from accounts.models import Profile

# Create your views here.
def index(request):
    search_term = request.GET.get('search')
    search_type = request.GET.get('search_type')
    min_salary = request.GET.get('min_salary')
    max_salary = request.GET.get('max_salary')

    jobs = Job.objects.all()

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
    }
    return render(request, 'home/index.html', {'template_data': template_data})

def about(request):
    return render(request, 'home/about.html')

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

    return redirect("home.show", id=job.id)

@login_required
def candidates(request):
    # Only recruiters can view

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

    # Searches
    search_skills = (request.GET.get("skills") or "").strip()
    search_location = (request.GET.get("location") or "").strip()
    search_projects = (request.GET.get("projects") or "").strip()

    if search_skills:
        profiles = profiles.filter(skills__icontains=search_skills)
    if search_location:
        profiles = profiles.filter(location__icontains=search_location)
    if search_projects:
        profiles = profiles.filter(projects__icontains=search_projects)

    safe_profiles = []
    for profile in profiles:
        if getattr(Profile, "Visibility", None) and profile.visibility == Profile.Visibility.PRIVATE:
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
        "search_projects": search_projects,
    }
    return render(request, "home/candidates.html", context)
