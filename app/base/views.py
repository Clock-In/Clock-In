from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpRequest
from django.http.request import QueryDict
from django.shortcuts import render
import datetime
from statistics import mean, stdev

from base import models
from base import queries
from base.auth import manager_only
from clockIn import utils

from .forms import ExtendedCustomUserChangeForm, ShiftCreationForm, ShiftSwapAcceptForm, ShiftSwapRequestForm

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


@login_required
def timetable_month(request):

    start_date = utils.query_timestamp(request, 'month_start')
    date, grouped_shifts = queries.get_shifts_for_month(start_date,
                                           for_user=request.user,
                                           fmt=queries.format_shift_for_user
                                           )
    month = date.strftime("%b")
    
    return render(request, 'user/timetable.html', {
        'month': month,
        'start_date': date,
        'weeks': grouped_shifts,
        'user': request.user,
        'year': date.year,
    })

def timetable_week(request):

    start_date = utils.query_timestamp(request, 'week_start')
    date, grouped_shifts = queries.get_shifts_for_week(start_date,
                                                       for_user=request.user,
                                                       fmt=queries.format_shift_for_user
                                                       )

    return render(
        request, 'user/timetable-week.html',
        {
            'week': [date + datetime.timedelta(days=i) for i in range(7)],
            'start_date': date,
            'shifts': grouped_shifts,
            'user': request.user,
        }
    )

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

    start_date = utils.query_timestamp(request, 'week_start')

    date, grouped_shifts = queries.get_shifts_for_week(start_date, fmt=queries.format_shift_for_admin)

    ctx = {
        "user": request.user,
        "form": form,
        "start_date": date,
        "shifts": grouped_shifts,
        "days": [date + datetime.timedelta(days=i) for i in range(7)] # for convenience in the frontend
    }
    return render(request, 'admin/create_shift.html', ctx)

def distribution(request):
    today = datetime.datetime.now()
    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")
    to_date = all_shifts.filter(end_at__range=[datetime.datetime.min, today]).order_by("-start_at", )
    
    day_distribution = {}
    day_distribution["sunday"] = to_date.filter(start_at__week_day=1).count()
    day_distribution["monday"] = to_date.filter(start_at__week_day=2).count()
    day_distribution["tuesday"] = to_date.filter(start_at__week_day=3).count()
    day_distribution["wednesday"] = to_date.filter(start_at__week_day=4).count()
    day_distribution["thursday"] = to_date.filter(start_at__week_day=5).count()
    day_distribution["friday"] = to_date.filter(start_at__week_day=6).count()
    day_distribution["saturday"] = to_date.filter(start_at__week_day=7).count()
    
    return render(request, 'user/distribution.html', {"days": day_distribution,})
    
def history(request):
    today = datetime.datetime.now()
    last_week = today - datetime.timedelta(weeks=1)
    month_start = today.replace(day=1)
    year_start = month_start.replace(month=1)
    

    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")

    scheduled = all_shifts.filter(end_at__range=[today, datetime.datetime.max])
    to_date = all_shifts.filter(end_at__range=[datetime.datetime.min, today]).order_by("-start_at", )
    past_week = all_shifts.filter(end_at__range=[last_week, today]).order_by("-start_at", )
    this_month_to_date = all_shifts.filter(end_at__range=[month_start, today]).order_by("-start_at", )
    this_year_to_date = all_shifts.filter(end_at__range=[year_start,today]).order_by("-start_at", )
    
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
    
    return render(request, 'user/history.html', {
        "week": {"shifts": past_week, "earnings": "{:.2f}".format(earnings_this_week) if earnings_to_date != None else 0 }, 
        "month": {"shifts": this_month_to_date, "earnings":  "{:.2f}".format(earnings_this_month) if earnings_to_date != None else 0 },
        "year": {"shifts": this_year_to_date, "earnings":  "{:.2f}".format(earnings_this_year) if earnings_to_date != None else 0 }, 
        "to_date": {"shifts": to_date, "earnings":  "{:.2f}".format(earnings_to_date) if earnings_to_date != None else 0 },
        "scheduled": scheduled,
    })
    
def earnings(request):
    today = datetime.datetime.now()
    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")
    to_date = all_shifts.filter(end_at__range=[datetime.datetime.min, today]).order_by("-start_at", )
    
    if to_date.count() != 0:
        aggregate = to_date.aggregate(time_elapsed=Sum(F("end_at") - F("start_at")))
        time_elapsed = aggregate["time_elapsed"] / datetime.timedelta(hours=1)
    else:
        time_elapsed = 0
        
        
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
    
    earnings_to_date = calculated_to_date.aggregate(
        total_sum=Sum('multiplied_result')
    )
    
    earnings = "0"
    
    if earnings_to_date["total_sum"] != None:
        earnings = "{:.2f}".format(earnings_to_date["total_sum"])          
        
    print(earnings)
    return render(request, 'user/earnings.html', {
        "to_date": {"shifts": to_date, "earnings": earnings },
        "elapsed":time_elapsed
    })    

@login_required
def shift_swap_request(request, pk):
    form = ShiftSwapRequestForm()
    if request.method == "POST":
        post_data: QueryDict = request.POST.copy()
        post_data.update({
            "shift": pk
        })
        form = ShiftSwapRequestForm(post_data)
        if form.is_valid():
            if form.cleaned_data['shift'].assigned_to.id == request.user.id:
                form.save()

    return render(
        request, 'shifts/swap_request.html',
        {
            "user": request.user,
            "form": form
        }
    )

@login_required
def view_shift_requests(request):
    form = ShiftSwapAcceptForm()
    if request.method == "POST":
        form = ShiftSwapAcceptForm(request.POST)
        if form.is_valid():
            req: models.ShiftSwapRequest = form.cleaned_data["request"] # type: ignore
            shift: models.Shift = req.shift # type: ignore
            if shift.role == request.user.role and shift.start_at > datetime.datetime.now().astimezone():
                req.active = False
                req.save()
                shift.completed_by = request.user
                shift.save()

    reqs = models.ShiftSwapRequest.objects\
            .filter(shift__role=request.user.role)\
            .filter(active=True)\
            .filter(shift__start_at__gt=datetime.datetime.now())\
            .order_by('shift__start_at')

    return render(
        request, 'shifts/swap_list.html',
        {
            "user": request.user,
            "num_requests": len(reqs),
            "requests": reqs,
            "form": form,
        }
    )

def manager_statistics(request):
    all_workers = models.User.objects.filter(is_staff=False)
        
    worker_distribution = []
    for worker in all_workers:
        worker_shifts = models.Shift.objects.filter(assigned_to=worker.id, end_at__range=[datetime.datetime.min, datetime.datetime.now()])
        worker_info = {}
        worker_info["name"] = worker.name
        worker_info["sunday"] = worker_shifts.filter(start_at__week_day=1).count()
        worker_info["saturday"] = worker_shifts.filter(start_at__week_day=7).count()
        worker_info["shift_count"] = worker_shifts.count()
        
        time_elapsed = worker_shifts.aggregate(time_elapsed=Sum(F("end_at") - F("start_at")))
        time_elapsed = time_elapsed["time_elapsed"] / datetime.timedelta(hours=1)
        
        worker_info["total"] = time_elapsed
        worker_distribution.append(worker_info)

    weekend_fairness = {}
    weekend_fairness["workers"] = []
    for worker in worker_distribution:
        weekend_fairness["workers"].append({"name": worker["name"], "score":worker["saturday"] + worker["sunday"] * 1.5})
    weekend_fairness["mean"] = mean([w["score"] for w in weekend_fairness["workers"]])
    weekend_fairness["stdev"] = stdev([w["score"] for w in weekend_fairness["workers"]])


    return render(request, "user/manager_statistics.html",{
        "employee_count": all_workers.count(),
        "worker_distribution": worker_distribution,
        "weekend_fairness": weekend_fairness
        })

class CustomLoginView(LoginView):
    form_class = LoginForm
