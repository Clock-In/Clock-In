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
from .forms import ExtendedCustomUserChangeForm
from django.db.models import Sum, F,FloatField, ExpressionWrapper
from django.db.models.functions import Cast

@login_required
def profile(request: HttpRequest):
    return render(request, "user/profile.html", {"user": request.user}) # type: ignore

def logout(request: HttpRequest):
    auth_logout(request)
    return render(request, 'registration/logged_out.html')

def my_shift(request,pk):
    shift = models.Shift.objects.get(id = pk)

    return render(request, 'user/myshift.html',{'shift':shift})


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
    for i in range(first_day):
        dayi = {'date':"",'weekday':i,'shift': 0}
        dayList.append(dayi)

    user_shifts = models.Shift.objects.filter(assigned_to=request.user)

    
    
    for day in range(1,num_days_in_month + 1):
        current_day = current_date.replace(day=day)
        current_weekday = current_day.weekday()
        shift_day = 0
        for shift in user_shifts:
            start = (shift.start_at)   

            if current_day.day == start.day:
                shift_day = shift

        dayi = {'date':day,'weekday':current_weekday,'shift':shift_day}
        dayList.append(dayi)

    weeks = [dayList[i:i+7] for i in range(0, len(dayList), 7)]
    
    return render(request, 'user/timetable.html',{'month':month,'weeks':weeks,'user':user})

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

    form = ShiftCreationForm()
    if request.method == "POST":
        form = ShiftCreationForm(request.POST)
        if form.is_valid():
            obj: models.Shift = form.save(commit=False)
            obj.role = obj.assigned_to.role if not form.cleaned_data.get('is_open') else form.cleaned_data.get('role') # type: ignore
            obj.save()
            if form.cleaned_data.get('is_open'):
                req = models.ShiftSwapRequest(shift=obj, message=form.cleaned_data.get('message'))
                req.save()

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
        if shift.assigned_to is None:
            shift.assigned_to = models.User(first_name='[Open]') # type: ignore
        grouped_shifts[start.weekday()].append(shift)
    ctx = {
        "user": request.user,
        "form": form,
        "start_date": start_date,
        "shifts": grouped_shifts,
        "days": [start_date + datetime.timedelta(days=i) for i in range(7)] # for convenience in the frontend
    }
    return render(request, 'admin/create_shift.html', ctx)

def statistics(request):
    #NOTE: should this be on client side?
    today = datetime.datetime.now()
    last_week = today - datetime.timedelta(weeks=1)
    month_start = today.replace(day=1)
    year_start = month_start.replace(month=1)
    

    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")

    if all_shifts.count() == 0:
        return render(request, "user/statistics.html", {"empty": True})
    
    scheduled = all_shifts.filter(end_at__range=[today, datetime.datetime.max])
    to_date = all_shifts.filter(end_at__range=[datetime.datetime.min, today])
    past_week = all_shifts.filter(end_at__range=[last_week, today])
    this_month_to_date = all_shifts.filter(end_at__range=[month_start, today])
    this_year_to_date = all_shifts.filter(end_at__range=[year_start,today])
         
    calculated_to_date = to_date.annotate(
        time_difference=ExpressionWrapper(
            Cast(F('end_at') - F('start_at'), output_field=FloatField()) / 3600000000, #convert to hours
            output_field=FloatField()
        ),
        multiplied_result=ExpressionWrapper(
            F('time_difference') * F('wage_multiplier') * Cast(F("assigned_to__role__hourly_rate"), output_field=FloatField()),
            output_field=FloatField()
        ),
    )
    
    earnings_this_week = calculated_to_date.filter(start_at__range=[last_week, today]).aggregate(
       total_sum=Sum('multiplied_result') 
    )
    
    earnings_this_month = calculated_to_date.filter(start_at__range=[month_start, today]).aggregate(
       total_sum=Sum('multiplied_result') 
    )
    
    earnings_this_year = calculated_to_date.filter(start_at__range=[year_start, today]).aggregate(
       total_sum=Sum('multiplied_result') 
    )
    
    earnings_to_date = calculated_to_date.aggregate(
        total_sum=Sum('multiplied_result')
    )

    earnings_to_date = earnings_to_date["total_sum"]
    earnings_this_week = earnings_this_week["total_sum"]
    earnings_this_month = earnings_this_month["total_sum"]
    earnings_this_year = earnings_this_year["total_sum"]
    
    if to_date.count() != 0:
        aggregate = to_date.aggregate(time_elapsed=Sum(F("end_at") - F("start_at")))
        time_elapsed = aggregate["time_elapsed"] / datetime.timedelta(hours=1)
    else:
        time_elapsed = 0
    

    
    return render(
        request, 'user/statistics.html', 
        {
            "user": request.user,
            "shifts": all_shifts,
            "week": {"shifts": past_week, "earnings": (round(earnings_this_week,2)) if earnings_to_date != None else 0 }, 
            "month": {"shifts": this_month_to_date, "earnings": (round(earnings_this_month,2)) if earnings_to_date != None else 0 },
            "year": {"shifts": this_year_to_date, "earnings": (round(earnings_this_year,2)) if earnings_to_date != None else 0 }, 
            "to_date": {"shifts": to_date, "earnings":(round(earnings_to_date,2)) if earnings_to_date != None else 0 },
            "scheduled": scheduled,
            "elapsed":time_elapsed, 
            })

class CustomLoginView(LoginView):
    form_class = LoginForm
