from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms import CustomUserCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
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