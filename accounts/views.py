from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
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
    template_data = {}
    template_data['title'] = 'Login'
    #If going to login form
    if request.method == 'GET':
        return render(request, 'accounts/login.html',
            {'template_data': template_data})
    elif request.method == 'POST':
        #check if user has correct username and passowrd
        user = authenticate(request, username = request.POST['username'], password = request.POST['password'])
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html',
                {'template_data': template_data})
        else:
            #login and authenticate user
            auth_login(request, user)
            return redirect('home.index')

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
            form.save()
            return redirect('accounts.login')
        else:
            #pass form and errors to template and render signup again
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})

# accounts/views.py
from accounts.models import Profile

@login_required
def privacy_settings(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)  # <- safe
    if request.method == "POST":
        form = PrivacySettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Privacy settings updated.")
            return redirect("accounts:privacy")
    else:
        form = PrivacySettingsForm(instance=profile)
    return render(request, "accounts/privacy_settings.html", {"form": form})

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
    }
    return render(request, "accounts/profile_detail.html", ctx)