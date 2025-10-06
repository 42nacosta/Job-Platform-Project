from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import CustomUserCreationForm, CustomErrorList, PrivacySettingsForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

# Create your views here.
@login_required
def logout(request):
    #logout and redirect to home
    auth_logout(request)
    return redirect('home.index')

def login(request):
    template_data = {'title': 'Login'}
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(next_url or 'home.index')
    else:
        form = AuthenticationForm(request)

    for field in form.fields.values():
        css_classes = field.widget.attrs.get('class', '')
        class_tokens = css_classes.split()
        if 'form-control' not in class_tokens:
            class_tokens.append('form-control')
        field.widget.attrs['class'] = ' '.join(class_tokens).strip()

    template_data['form'] = form
    if next_url:
        template_data['next'] = next_url

    return render(request, 'accounts/login.html', {'template_data': template_data})

def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    #if going to signup form
    if request.method == 'GET':
        #use custom form
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    elif request.method == 'POST':
        #create new form to store user info
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        #check if form is correct (same password, not common password, etc) and save user
        if form.is_valid():
            user = form.save()  # save the User instance

            is_recruiter = form.cleaned_data.get("is_recruiter", False)
            user.profile.is_recruiter = is_recruiter
            user.profile.save()
            return redirect('accounts:login')
        else:
            #pass form and errors to template and render signup again
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})

# accounts/views.py
from accounts.models import Profile
from home.recommendations import generate_job_recommendations

@login_required
def privacy_settings(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)  # <- safe
    if request.method == "POST":
        form = PrivacySettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Privacy settings updated.")

            # PSEUDOCODE: After profile update, regenerate job recommendations for job seekers
            # Calls recommendation engine to find matching jobs based on updated skills/location
            if not profile.is_recruiter:
                generate_job_recommendations(request.user)

            return redirect("accounts:privacy")
    else:
        form = PrivacySettingsForm(instance=profile)
    return render(request, "accounts/privacy_settings.html", {"form": form, "profile": profile})

def profile_detail(request, username):
    owner = get_object_or_404(User, username=username)
    profile = owner.profile
    viewer = request.user if request.user.is_authenticated else None
    ctx = {
        "owner": owner,
        "profile": profile,
        "viewer": viewer,
        # convenience flags if you prefer not to call methods in templates
        "can_email": profile.can_view(viewer, "email"),
        "can_phone": profile.can_view(viewer, "phone"),
        "can_resume": profile.can_view(viewer, "resume"),
        "can_education": profile.can_view(viewer, "education"),
        "can_experience": profile.can_view(viewer, "experience"),
        "can_location": profile.can_view(viewer, "location"),
        "can_skills": profile.can_view(viewer, "skills"),
        "can_projects": profile.can_view(viewer, "projects"),
        "can_firstName": profile.can_view(viewer, "firstName"),
        "can_lasttName": profile.can_view(viewer, "lastName"),
    }
    return render(request, "accounts/profile_detail.html", ctx)
