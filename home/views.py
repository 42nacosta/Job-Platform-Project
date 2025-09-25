from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Job
from django.contrib.auth.decorators import login_required
from decimal import Decimal

# Create your views here.
def index(request):
    search_term = request.GET.get('search')
    search_type = request.GET.get('search_type')
    min_salary = request.GET.get('min_salary')
    max_salary = request.GET.get('max_salary')

    jobs = Job.objects.all()

    if search_term:
        if search_type == 'title':
            jobs = Job.objects.filter(title__icontains=search_term)
        elif search_type == 'location':
            jobs = Job.objects.filter(location__icontains=search_term)
        elif search_type == 'category':
            jobs = Job.objects.filter(category__icontains=search_term)
        else:
            jobs = Job.objects.filter(title__icontains=search_term)
    if min_salary:
        jobs = Job.objects.filter(salary__gte=min_salary)
    if max_salary:
        jobs = Job.objects.filter(salary__lte=max_salary)

    template_data = {}
    template_data['title'] = 'Jobs'
    template_data['jobs'] = jobs
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
