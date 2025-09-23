from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib.auth.decorators import login_required
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
    job =  Job.objects.get(id=id)
    template_data = {}
    template_data['title'] = job.title
    template_data['job'] = job
    return render(request, 'home/show.html',
                  {'template_data': template_data})