from django.core.mail import send_mail
from django.utils import timezone 
from datetime import timedelta 
from .models import Shift
from . import settings

def email_sending():
    time_now=timezone.now()
    after_two_hours=time_now+timedelta(hours=2)
    upcoming_shift=Shift.objects.filter(start_at__gte=time_now,start_at__lte=after_two_hours)
    for soon_shifts in upcoming_shift:
        if soon_shifts.assigned_to.recieve_shift_reminders:
            employee_email=soon_shifts.assigned_to.email
            employee_name=soon_shifts.assigned_to.first_name
            
            subject="Upcoming Shift Reminder"
            message=f'Hello {employee_name} your shift starts in two hours'
            sender_email=settings.EMAIL_HOST_USER
            employee_having_shift=[employee_email]
            try:
                send_mail(subject, message, sender_email, employee_having_shift)
            except Exception:
                pass

email_sending()