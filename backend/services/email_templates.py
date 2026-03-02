"""Email HTML templates for OTP and booking notifications."""


def _wrap(body_content: str) -> str:
    """Wrap content in a minimal HTML email layout."""
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:24px 0;">
<tr><td align="center">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:8px;border:1px solid #e5e5e5;">
<tr><td style="padding:32px 24px;">
<h2 style="margin:0 0 24px;color:#1a1a1a;font-size:20px;">OneSpot</h2>
{body_content}
</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid #e5e5e5;">
<p style="margin:0;color:#999;font-size:12px;">OneSpot — Community parking sharing at One Maidenhead</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def render_otp(code: str) -> tuple[str, str]:
    """Return (subject, html) for an OTP email."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your login code is:</p>
<p style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1a1a1a;text-align:center;
   margin:16px 0;padding:16px;background:#f5f5f5;border-radius:8px;">{code}</p>
<p style="color:#666;font-size:14px;margin:16px 0 0;">This code expires in 5 minutes. If you didn't request this, ignore this email.</p>"""
    return ("Your OneSpot login code", _wrap(body))


def render_booking_confirmed_booker(*, bay: str, date: str, start: int, end: int) -> tuple[str, str]:
    """Return (subject, html) for booking confirmation sent to the booker."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your booking is confirmed.</p>
<table style="width:100%;border-collapse:collapse;margin:8px 0;">
<tr><td style="padding:8px 0;color:#666;">Bay</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{bay}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Date</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{date}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Time</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{start}:00 — {end}:00</td></tr>
</table>"""
    return (f"Booking confirmed — Bay {bay}", _wrap(body))


def render_booking_confirmed_owner(*, bay: str, date: str, start: int, end: int, booker_name: str) -> tuple[str, str]:
    """Return (subject, html) for booking notification sent to the bay owner."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your bay has been booked.</p>
<table style="width:100%;border-collapse:collapse;margin:8px 0;">
<tr><td style="padding:8px 0;color:#666;">Bay</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{bay}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Booked by</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{booker_name}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Date</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{date}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Time</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{start}:00 — {end}:00</td></tr>
</table>"""
    return (f"Your bay {bay} has been booked", _wrap(body))


def render_booking_ending_reminder(*, bay: str, end_time: str) -> tuple[str, str]:
    """Return (subject, html) for booking ending reminder."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your booking is ending soon.</p>
<p style="color:#333;font-size:16px;margin:0 0 8px;">Bay <strong>{bay}</strong> ends at <strong>{end_time}</strong>.</p>
<p style="color:#666;font-size:14px;margin:16px 0 0;">Please move your car before the booking ends.</p>"""
    return (f"Booking ending soon — Bay {bay}", _wrap(body))


def render_booking_cancelled(*, bay: str, date: str) -> tuple[str, str]:
    """Return (subject, html) for booking cancellation."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">A booking has been cancelled.</p>
<table style="width:100%;border-collapse:collapse;margin:8px 0;">
<tr><td style="padding:8px 0;color:#666;">Bay</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{bay}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Date</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{date}</td></tr>
</table>"""
    return (f"Booking cancelled — Bay {bay}", _wrap(body))
