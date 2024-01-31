from django.shortcuts import render
from django.http import HttpResponse


def settings(request):
    return render(request, 'base/settings.html', {})

def timetable(request):
    return HttpResponse("Placeholder for timetable page")
