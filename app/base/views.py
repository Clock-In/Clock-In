from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpRequest
from django.http.request import QueryDict
from django.shortcuts import render, redirect, get_object_or_404


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
    all_shifts = models.Shift.objects.filter(assigned_to=request.user)
    today = datetime.datetime.now()
    scheduled = all_shifts.filter(start_at__range=[today, datetime.datetime.max]).order_by("start_at")
    
    if scheduled.count() == 0:
        return render(request, "user/profile.html", {"user": request.user, "next": None})
       
    return render(request, "user/profile.html", {"user": request.user, "next": scheduled.first()}) # type: ignore

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

@login_required
def distribution(request):
    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")

    today = datetime.datetime.now()
    to_date = all_shifts.filter(end_at__range=[datetime.datetime.min, today]).order_by("-start_at", )
    
    if to_date.count() == 0:
        return render(request, 'user/distribution.html', {"empty": True})
    
    day_distribution = {}
    day_distribution["sunday"] = to_date.filter(start_at__week_day=1).count()
    day_distribution["monday"] = to_date.filter(start_at__week_day=2).count()
    day_distribution["tuesday"] = to_date.filter(start_at__week_day=3).count()
    day_distribution["wednesday"] = to_date.filter(start_at__week_day=4).count()
    day_distribution["thursday"] = to_date.filter(start_at__week_day=5).count()
    day_distribution["friday"] = to_date.filter(start_at__week_day=6).count()
    day_distribution["saturday"] = to_date.filter(start_at__week_day=7).count()
    
    return render(request, 'user/distribution.html', {"days": day_distribution,})
   
@login_required 
def history(request, period):
    today = datetime.datetime.now()
    last_week = today - datetime.timedelta(weeks=1)
    month_start = today.replace(day=1)
    year_start = month_start.replace(month=1)
    

    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")
    
    calculated_to_date = all_shifts.annotate(
        time_difference=ExpressionWrapper(
            Cast(F('end_at') - F('start_at'), output_field=FloatField()) / 3600000000, #convert to hours
            output_field=FloatField()
        ),
        multiplied_result=ExpressionWrapper(
            F('time_difference') * F('wage_multiplier') * Cast(F("assigned_to__role__hourly_rate"), output_field=FloatField()),
            output_field=FloatField()
        ),
    )

    if period == "week":
        shifts = all_shifts.filter(end_at__range=[last_week, today]).order_by("-start_at")
        earnings = calculated_to_date.filter(start_at__range=[last_week, today]).aggregate(total_sum=Sum('multiplied_result'))
        message = "In the last 7 days"
        
    elif period == "month":
        shifts = all_shifts.filter(end_at__range=[month_start, today]).order_by("-start_at")
        earnings = calculated_to_date.filter(start_at__range=[month_start, today]).aggregate(total_sum=Sum('multiplied_result'))
        message = "This month so far"
    else:
        shifts = all_shifts.filter(end_at__range=[year_start,today]).order_by("-start_at")
        earnings = calculated_to_date.filter(start_at__range=[year_start, today]).aggregate(total_sum=Sum('multiplied_result'))
        message = "This year so far"
    
    earnings = earnings["total_sum"]   
    
    return render(request, 'user/history.html', {
        "shifts": shifts,
        "earnings": "{:.2f}".format(earnings) if earnings != None else 0,
        "message": message
    })
    
    
def calculate_earnings(shifts):
    time_elapsed = 0
    earnings = "0"
    
    if shifts.count() == 0:
        return (time_elapsed, earnings)
    
    aggregate = shifts.aggregate(time_elapsed=Sum(F("end_at") - F("start_at")))
    time_elapsed = aggregate["time_elapsed"] / datetime.timedelta(hours=1)
    
    shifts = shifts.annotate(
        time_difference=ExpressionWrapper(
            Cast(F('end_at') - F('start_at'), output_field=FloatField()) / 3600000000, #convert to hours
            output_field=FloatField()
        ),
        multiplied_result=ExpressionWrapper(
            F('time_difference') * F('wage_multiplier') * Cast(F("assigned_to__role__hourly_rate"), output_field=FloatField()),
            output_field=FloatField()
        ),
    )    
    
    shifts = shifts.aggregate(
        total_sum=Sum('multiplied_result')
    )
    
    if shifts["total_sum"] != None:
        earnings = "{:.2f}".format(shifts["total_sum"]) 
        
    return (time_elapsed, earnings)

@login_required
def earnings(request):
    if request.user.is_staff:
        return breakdown(request)
    
    all_shifts = models.Shift.objects.filter(assigned_to=request.user).order_by("start_at")

    if all_shifts.count() == 0:
        return render(request, 'user/earnings.html', {
            "to_date": {"shifts": all_shifts, "earnings": "0" },
            "elapsed":0,
            "scheduled_earnings": {"month": "0", "year": "0"}
        })

    today = datetime.datetime.now()
    to_date = all_shifts.filter(end_at__range=[datetime.datetime.min, today])
    scheduled_shifts = all_shifts.filter(end_at__range=[today, datetime.datetime.max])
    
    (time_elapsed, earnings) = calculate_earnings(to_date)
    
    if scheduled_shifts.count() == 0:
        return render(request, 'user/earnings.html', {
            "to_date": {"shifts": to_date, "earnings": earnings },
            "elapsed":time_elapsed,
            "scheduled_earnings": {"month": "0", "year": "0"},
            "scheduled_hours": {"month": "0", "year": "0"}
        })
    
    scheduled_shifts_month = scheduled_shifts.filter(start_at__range=[today, today.replace(day=1, month=(today.month+1) % 12)])
    scheduled_shifts_year = scheduled_shifts.filter(start_at__range=[today, datetime.date(today.year+1, 1, 1)])
    
    scheduled_earnings = {}
    scheduled_hours = {}
    (scheduled_hours["month"],scheduled_earnings["month"]) = calculate_earnings(scheduled_shifts_month)
    (scheduled_hours["year"], scheduled_earnings["year"]) = calculate_earnings(scheduled_shifts_year)

    return render(request, 'user/earnings.html', {
        "to_date": {"shifts": to_date, "earnings": earnings },
        "elapsed":time_elapsed,
        "scheduled_earnings": scheduled_earnings,
        "scheduled_hours": scheduled_hours
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
            if shift.role == request.user.role and shift.start_at > datetime.datetime.now():
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
    
@login_required
@manager_only
def breakdown(request):
    all_workers = models.User.objects.filter(is_staff=False)
    worker_distribution = []       

    for worker in all_workers:
        worker_shifts = models.Shift.objects.filter(assigned_to=worker.id, end_at__range=[datetime.datetime.min, datetime.datetime.now()])

        if worker_shifts.count() == 0:
            continue

        worker_info = {}
        worker_info["name"] = worker.name
        worker_info["shift_count"] = worker_shifts.count()
        worker_info["sunday"] = worker_shifts.filter(start_at__week_day=1).count()
        worker_info["saturday"] = worker_shifts.filter(start_at__week_day=7).count()
        
        time_elapsed = worker_shifts.aggregate(time_elapsed=Sum(F("end_at") - F("start_at")))
        time_elapsed = time_elapsed["time_elapsed"] / datetime.timedelta(hours=1)
        
        worker_info["total"] = time_elapsed
        worker_info["score"] = worker_info["saturday"] + worker_info["sunday"] * 1.5
    
        worker_distribution.append(worker_info)
    
    max_score = 0
    max_worker = ""
    max_hours = 0
    max_hours_worker = ""

    for worker in worker_distribution:
        if worker["score"] > max_score:
            max_score = worker["score"]
            max_worker = worker["name"]
        if worker["total"] > max_hours:
            max_hours = worker["total"]
            max_hours_worker = worker["name"]
            
        
        
    return render(request, "user/breakdown.html", {
        "employee_count": all_workers.count(),
        "worker_distribution": worker_distribution,
        "max_worker": max_worker,
        "max_hours_worker": max_hours_worker
    })
    


class CustomLoginView(LoginView):
    form_class = LoginForm


@login_required
@manager_only
def delete_shift(request, pk):
    shift = get_object_or_404(models.Shift, pk=pk)
    if request.method == 'POST':
        shift.delete()
        return redirect('/timetable/create')  # Redirect to the timetable page after deletion
    return render(request, 'shift/delete.html', {'shift': shift})

@login_required
@manager_only
def edit_shift(request, pk):
    shift = get_object_or_404(models.Shift, pk=pk)
    form = ShiftCreationForm(instance=shift)
    if request.method == 'POST':
        form = ShiftCreationForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('/timetable/create')  # Redirect to the timetable page after editing
    return render(request, 'admin/edit_shift.html', {'form': form, 'shift': shift})

def index(request):
    if request.user.is_authenticated:
        return redirect('/accounts/profile/')
    else:
        return redirect('/accounts/login/')

