from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib.auth.decorators import login_required
# Create your views here.
def index(request):
    search_term = request.GET.get('search')
    if search_term:
        jobs = Job.objects.filter(name__icontains=search_term)
    else:
        jobs = Job.objects.all()
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