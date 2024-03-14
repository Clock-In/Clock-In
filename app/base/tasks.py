from django.core.mail import send_mail
from django.utils import timezone 
from datetime import timedelta 
from .models import Shift
from . import settings
import logging

logging.BaseConfig( level = logging.ERROR, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename = 'email_sending.log', filemode = 'a')
logger = logging.getLogger(__file__)

def email_sending():
    time_now=timezone.now()
    after_two_hours=time_now+timedelta(hours =2 )
    upcoming_shift=Shift.objects.filter(start_at__gte = time_now,start_at__lte = after_two_hours)


    for soon_shifts in upcoming_shift:
        recipient = soon_shifts.completed_by if soon_shifts.completed_by else soon_shifts.assigned_to

        if recipient.recieve_shift_reminders:
            employee_email = recipient.email
            employee_name = recipient.name
            
            subject="Upcoming Shift Reminder"
            message=(f'Hello {employee_name}\n\n',
                     f"This is a reminder about your scheduled shift today. Please note that your shift begins in two hours at {soon_shifts.start_at.strftime('%I:%M %P')}.")
            sender_email=settings.EMAIL_HOST_USER
            employee_having_shift=[employee_email]
            try:
                send_mail(subject, message, sender_email, employee_having_shift)
            except Exception as e:
                error_message = f"An error has occured while sending a shift reminder email to {employee_name}: {e}\n"
                logger.error(error_message)

email_sending()