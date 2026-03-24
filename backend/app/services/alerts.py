"""
Email service for job alerts — uses local MailHog SMTP by default.

View captured emails at http://localhost:8025
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.models import Alert, Job

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, body_html: str, body_text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.sendmail(settings.from_email, [to], msg.as_string())

    logger.info("Email sent to %s — %s", to, subject)


def send_confirmation_email(alert: "Alert") -> None:
    confirm_url = f"{settings.base_url}/api/v1/alerts/confirm/{alert.confirm_token}"

    body_text = (
        f"Confirm your JobScraper alert for: {alert.query}\n\n"
        f"Click here to confirm: {confirm_url}\n\n"
        "If you didn't request this, ignore this email."
    )
    body_html = f"""
<html><body style="font-family:sans-serif;max-width:560px;margin:auto">
  <h2>Confirm your job alert</h2>
  <p>You subscribed to alerts for: <strong>{alert.query}</strong></p>
  <p>
    <a href="{confirm_url}"
       style="background:#2563eb;color:#fff;padding:10px 20px;
              border-radius:6px;text-decoration:none;display:inline-block">
      Confirm alert
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px">
    Or copy this link: {confirm_url}
  </p>
</body></html>
"""
    _send(alert.email, f"Confirm your alert: {alert.query}", body_html, body_text)


def send_digest_email(alert: "Alert", jobs: list["Job"]) -> None:
    if not jobs:
        return

    unsubscribe_url = f"{settings.base_url}/alerts/{alert.id}/unsubscribe"

    job_rows_html = "\n".join(
        f"""<tr>
          <td style="padding:8px 0;border-bottom:1px solid #e5e7eb">
            <a href="{job.url}" style="color:#2563eb;font-weight:600">{job.title}</a><br>
            <span style="color:#374151">{job.company}</span>
            {f' &middot; <span style="color:#6b7280">{job.location}</span>' if job.location else ''}
          </td>
        </tr>"""
        for job in jobs
    )

    job_rows_text = "\n".join(
        f"- {job.title} at {job.company}{f' ({job.location})' if job.location else ''}\n  {job.url}"
        for job in jobs
    )

    body_text = (
        f"New jobs matching: {alert.query}\n\n"
        f"{job_rows_text}\n\n"
        f"Unsubscribe: {unsubscribe_url}"
    )
    body_html = f"""
<html><body style="font-family:sans-serif;max-width:560px;margin:auto">
  <h2>New jobs matching <em>{alert.query}</em></h2>
  <table style="width:100%;border-collapse:collapse">
    {job_rows_html}
  </table>
  <p style="margin-top:24px;color:#6b7280;font-size:12px">
    <a href="{unsubscribe_url}" style="color:#6b7280">Unsubscribe</a>
  </p>
</body></html>
"""
    subject = f"{len(jobs)} new job{'s' if len(jobs) != 1 else ''} matching: {alert.query}"
    _send(alert.email, subject, body_html, body_text)
