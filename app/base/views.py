from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from datetime import datetime, timedelta, date
import calendar

from .forms import ExtendedCustomUserChangeForm
from base.models import Shift
from django.db.models import Sum, F,FloatField, ExpressionWrapper
from django.db.models.functions import Cast

@login_required
def profile(request: HttpRequest):
    return render(request, "user/profile.html", {"user": request.user}) # type: ignore

def logout(request: HttpRequest):
    auth_logout(request)
    return render(request, 'registration/logged_out.html')

def time_table_page(request):
    current_date = datetime.now()

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
def statistics(request):
    #NOTE: should this be on client side?
    today = date.today()
    last_week = today - timedelta(weeks=1)
    month_start = today.replace(day=1)
    year_start = month_start.replace(month=1)
    

    all_shifts = Shift.objects.filter(assigned_to=request.user).order_by("start_at")

    if all_shifts.count() == 0:
        return render(request, "user/statistics.html", {"empty": True})
    
    scheduled = all_shifts.filter(start_at__range=[today, datetime.max])
    to_date = all_shifts.filter(start_at__range=[datetime.min, today])
    past_week = all_shifts.filter(start_at__range=[last_week, today])
    this_month_to_date = all_shifts.filter(start_at__range=[month_start, today])
    this_year_to_date = all_shifts.filter(start_at__range=[year_start,today])
         
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
        time_elapsed = aggregate["time_elapsed"] / timedelta(hours=1)
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