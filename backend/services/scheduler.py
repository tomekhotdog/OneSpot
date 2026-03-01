"""Reminder scheduler — checks for bookings ending soon and sends WhatsApp reminders."""

import logging
from datetime import datetime, date as date_type

from apscheduler.schedulers.background import BackgroundScheduler

from backend.state import state_manager
from backend.services.whatsapp import send_message

logger = logging.getLogger(__name__)


def check_upcoming_reminders():
    """Check for bookings ending in 25-35 minutes, send reminders."""
    now = datetime.utcnow()
    state = state_manager.read()

    for booking in state.bookings.values():
        if booking.status != "confirmed" or booking.reminder_sent:
            continue
        booking_date = date_type.fromisoformat(booking.date)
        end_dt = datetime.combine(
            booking_date, datetime.min.time().replace(hour=booking.end_hour)
        )
        time_until_end = (end_dt - now).total_seconds() / 60

        if 25 <= time_until_end <= 35:
            booker = state.users.get(booking.booker_user_id)
            if booker:
                try:
                    send_message(
                        phone=booker.phone,
                        template="booking_ending_reminder",
                        params={
                            "bay": booking.bay_number,
                            "end_time": f"{booking.end_hour}:00",
                        },
                        state_manager=state_manager,
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send reminder for booking {booking.id}: {e}"
                    )
                    continue

            def mark_sent(s, bid=booking.id):
                if bid in s.bookings:
                    s.bookings[bid].reminder_sent = True
                return s

            state_manager.update(mark_sent)
            logger.info(f"Sent reminder for booking {booking.id}")


def start_scheduler():
    """Start the background scheduler for reminder checks."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_reminders, "interval", minutes=5)
    scheduler.start()
    logger.info("Reminder scheduler started (5-minute interval)")
    return scheduler
