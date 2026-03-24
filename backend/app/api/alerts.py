"""Alert subscription endpoints (Phase 3 — stubs ready for Phase 1)."""

from __future__ import annotations

import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Alert
from app.schemas import AlertCreate, AlertRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertRead, status_code=201)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Subscribe an email to a saved search query."""
    confirm_token = secrets.token_urlsafe(32)
    alert = Alert(
        email=payload.email,
        query=payload.query,
        filters=payload.filters,
        frequency=payload.frequency,
        confirm_token=confirm_token,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    try:
        from app.services.alerts import send_confirmation_email
        send_confirmation_email(alert)
    except Exception as exc:
        logger.warning("Failed to send confirmation email: %s", exc)

    return AlertRead.model_validate(alert)


@router.get("/confirm/{token}", response_model=AlertRead)
async def confirm_alert(token: str, db: AsyncSession = Depends(get_db)):
    """Confirm an alert subscription via magic link token."""
    result = await db.execute(select(Alert).where(Alert.confirm_token == token))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    alert.confirmed = True
    alert.confirm_token = None
    await db.commit()
    return AlertRead.model_validate(alert)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Unsubscribe / deactivate an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = False
    await db.commit()
