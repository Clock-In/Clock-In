
import datetime
import typing

from django.db.models import Q
from base import models


def format_shift_for_admin(shift: models.Shift) -> models.Shift:
    if shift.assigned_to is None:
        shift.assigned_to = models.User(first_name='[Open]')
    elif shift.completed_by is not None and shift.assigned_to != shift.completed_by:
        display_user = models.User(first_name=f"[{shift.assigned_to}]⟶[{shift.completed_by}]")
        shift.assigned_to = display_user
    return shift

def format_shift_for_user(shift: models.Shift) -> models.Shift:
    # TODO: label swaps?
    return shift


def _nofmt(x):
   return x


def get_shifts_for_month(
        date: datetime.datetime,
        for_user: typing.Optional[models.User] = None,
        fmt: typing.Callable = _nofmt
):

    if date.timestamp() == 0:
        date = datetime.datetime.now(datetime.timezone.utc)
    date += datetime.timedelta(days=-(date.day - 1))
    date = datetime.datetime.combine(date, datetime.time(0))
    week_date = date
    weeks = []
    while week_date.month == date.month:
        week_date, shifts = get_shifts_for_week(week_date, for_user, fmt)
        weeks.append([
            (week_date + datetime.timedelta(days=i), z) if (week_date + datetime.timedelta(days=i)
                  ).month == date.month else (None, [])
            for i, z in enumerate(shifts)
        ])
        week_date += datetime.timedelta(days=7)

    return date, weeks

def get_shifts_for_week(
        date: datetime.datetime,
        for_user: typing.Optional[models.User] = None,
        fmt: typing.Callable = _nofmt
) -> typing.Tuple[datetime.datetime, typing.List[typing.List[models.Shift]]]:

    if date.timestamp() == 0:
        date = datetime.datetime.today()
    date += datetime.timedelta(days=-date.weekday())  # get most recent monday
    date = datetime.datetime.combine(date, datetime.time(0))
    end = date + datetime.timedelta(days=7)
    end -= datetime.timedelta(seconds=1) # prevents shift starting at 00:00 of the next week from being included
    shifts = get_shifts(date, end, for_user)
    grouped = [[] for _ in range(7)]
    for shift in shifts:
        start: datetime.datetime = shift.start_at  # type: ignore
        grouped[start.weekday()].append(fmt(shift))
    return date, grouped


def get_shifts(start_date: datetime.datetime, end_date: datetime.datetime, for_user: typing.Optional[models.User] = None) -> typing.List[models.Shift]:
    query = Q(start_at__range=[start_date, end_date])
    if for_user is not None:
        # Include/exclude shift swaps:
        # If assigned_to != completed_by AND completed_by != null,
        # then the shift has been swapped.
        no_swap_query = Q(assigned_to=for_user)
        no_swap_query.add(Q(completed_by=None), Q.AND)
        query.add(Q(completed_by=for_user) | no_swap_query, Q.AND)
    queryset = models.Shift.objects.filter(query).order_by('start_at')

    return queryset

