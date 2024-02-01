from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

@login_required
def profile(request: HttpRequest):
    return render(request, "user/profile.html", {"user": request.user}) # type: ignore

def logout(request: HttpRequest):
    auth_logout(request)
    return render(request, 'registration/logged_out.html')
