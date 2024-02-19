from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpRequest
from django.shortcuts import render
import calendar
import datetime

from base import models
from base.auth import manager_only
from clockIn import utils

from .forms import ExtendedCustomUserChangeForm, ShiftCreationForm

from base.forms import LoginForm

@login_required
def profile(request: HttpRequest):
    return render(request, "user/profile.html", {"user": request.user}) # type: ignore

def logout(request: HttpRequest):
    auth_logout(request)
    return render(request, 'registration/logged_out.html')

def time_table_page(request):
    current_date = datetime.datetime.now()

    user = request.user

    #MONTH HANDLING
    monthNum = current_date.month
    months = ["January","February","March","April","May","June",
    "July","August","September","October","November","December"]
    
    month = months[monthNum-1]

    year = current_date.year
    day = current_date.day
    hour = current_date.hour
    num_days_in_month = calendar.monthrange(year, monthNum)[1]
    dayList = []

    first_day = current_date.replace(day=1)
    first_day = first_day.weekday()
    print(first_day)
    for i in range(first_day):
        dayi = {'date':"",'weekday':i}
        dayList.append(dayi)

    row = 0
    #lunes = 0
    
    for day in range(1,num_days_in_month + 1):
        current_day = current_date.replace(day=day)
        current_weekday = current_day.weekday()
        dayi = {'date':day,'weekday':current_weekday}
        dayList.append(dayi)

    weeks = [dayList[i:i+7] for i in range(0, len(dayList), 7)]
    

    return render(request, 'user/timetable.html',{'month':month,'weeks':weeks})

@login_required
def settings(request):
    if request.method == "POST":
        user_form = ExtendedCustomUserChangeForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
    else:
        user_form = ExtendedCustomUserChangeForm(instance=request.user)
    return render(request, 'user/settings.html', {"user": request.user, "user_form": user_form,})

@login_required
@manager_only
def create_timetable(request):

    if request.method == "POST":
        form = ShiftCreationForm(request.POST)
        if form.is_valid():
            obj: models.Shift = form.save(commit=False)
            obj.role = obj.assigned_to.role # type: ignore
            obj.save()
    else:
        form = ShiftCreationForm()
    start_date = datetime.datetime.fromtimestamp(utils.int_or_zero(request.GET.get('week_start', 0)))
    if start_date.timestamp() == 0:
        start_date = datetime.datetime.today()
        start_date += datetime.timedelta(days=-start_date.weekday()) # get most recent monday
        start_date = datetime.datetime.combine(start_date, datetime.time(0))
    shifts: list[models.Shift] = models.Shift.objects.filter( # type: ignore
        start_at__range=[start_date, start_date + datetime.timedelta(days=6)]
    ).order_by('start_at')
    grouped_shifts = [[] for _ in range(7)]
    for shift in shifts:
        start: datetime.datetime = shift.start_at # type: ignore
        grouped_shifts[start.weekday()].append(shift)
    ctx = {
        "user": request.user,
        "form": form,
        "start_date": start_date,
        "shifts": grouped_shifts,
        "days": [start_date + datetime.timedelta(days=i) for i in range(7)] # for convenience in the frontend
    }
    return render(request, 'admin/create_shift.html', ctx)

class CustomLoginView(LoginView):
    form_class = LoginForm
