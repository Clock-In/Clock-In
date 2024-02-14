from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from datetime import datetime
from .models import User,Shift,Role
import calendar
from django.db.models import Q

@login_required
def profile(request: HttpRequest):
    return render(request, "user/profile.html", {"user": request.user}) # type: ignore

def logout(request: HttpRequest):
    auth_logout(request)
    return render(request, 'registration/logged_out.html')

def my_shift(request,pk):
    shift = Shift.objects.get(id = pk)

    return render(request, 'user/myshift.html',{'shift':shift})


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
        dayi = {'date':"",'weekday':i,'shift': 0}
        dayList.append(dayi)

    row = 0
    #lunes = 0

    user_shifts = Shift.objects.filter(assigned_to=request.user)

    
    
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
    print(weeks)
    # for week in weeks:
    #     for day in week:
    #         print(day["shift"])

    #//////////////////SHIFT HANDLING///////////////////////////////////
    
    print(user.email)


        #print(shift.start_at)
    
    return render(request, 'user/timetable.html',{'month':month,'weeks':weeks,'user':user})
