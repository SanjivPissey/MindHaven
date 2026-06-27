import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Appointment

logger = logging.getLogger(__name__)

def send_appointment_reminders():
    """Job to check for upcoming appointments and send email reminders."""
    now = timezone.localtime(timezone.now())
    
    # Check for appointments 24 hours away
    target_time_24h = now + timedelta(hours=24)
    # Give a 5-minute window for the query
    window_start_24h = target_time_24h - timedelta(minutes=2)
    window_end_24h = target_time_24h + timedelta(minutes=3)
    
    # Wait, instead of calculating window via exact datetime matching against DateField + TimeField,
    # let's iterate through un-reminded Scheduled appointments and check the time difference.
    
    appointments = Appointment.objects.filter(status='Scheduled')
    
    for appt in appointments:
        # Combine date and time to a timezone-aware datetime object
        appt_datetime = timezone.make_aware(timezone.datetime.combine(appt.date, appt.time))
        time_diff = appt_datetime - now
        
        # 24 hour reminder
        if not appt.reminder_24h_sent and timedelta(hours=23, minutes=55) <= time_diff <= timedelta(hours=24, minutes=5):
            subject = f"Reminder: Upcoming Appointment with {appt.psychologist.fullname}"
            message = (
                f"Dear {appt.user.fullname},\n\n"
                f"This is a reminder that you have an appointment scheduled with {appt.psychologist.fullname} "
                f"tomorrow at {appt.time.strftime('%I:%M %p')}.\n\n"
                f"You can join the session using this link: {appt.meet_link}\n\n"
                f"Best regards,\nMindEase Team"
            )
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [appt.user.email])
                appt.reminder_24h_sent = True
                appt.save()
                logger.info(f"Sent 24h reminder to {appt.user.email}")
            except Exception as e:
                logger.error(f"Failed to send 24h reminder to {appt.user.email}: {e}")
                
        # 1 hour reminder
        if not appt.reminder_1h_sent and timedelta(minutes=55) <= time_diff <= timedelta(hours=1, minutes=5):
            subject = f"Reminder: Your Appointment Starts in 1 Hour"
            message = (
                f"Dear {appt.user.fullname},\n\n"
                f"Your appointment with {appt.psychologist.fullname} will start in exactly 1 hour at {appt.time.strftime('%I:%M %p')}.\n\n"
                f"Join the session here: {appt.meet_link}\n\n"
                f"Best regards,\nMindEase Team"
            )
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [appt.user.email])
                appt.reminder_1h_sent = True
                appt.save()
                logger.info(f"Sent 1h reminder to {appt.user.email}")
            except Exception as e:
                logger.error(f"Failed to send 1h reminder to {appt.user.email}: {e}")

def start():
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    # Run the job every 5 minutes
    scheduler.add_job(send_appointment_reminders, 'interval', minutes=5, id='send_reminders', replace_existing=True)
    scheduler.start()
    logger.info("APScheduler started.")
