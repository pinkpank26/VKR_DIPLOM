import time
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from .config import settings
from .smtp_client import send_email
from .models import Message, Contact, Unsubscribe, SendLog, Campaign


def _is_unsubscribed(db: Session, contact_id: int) -> bool:
    q = select(Unsubscribe.id).where(Unsubscribe.contact_id == contact_id)
    return db.execute(q).first() is not None


def build_messages_for_campaign(db: Session, campaign_id: int) -> int:
    camp = db.get(Campaign, campaign_id)
    if not camp or not camp.template:
        return 0

    tpl_subject = camp.template.subject or ""
    tpl_body = camp.template.body or ""

    contacts = db.execute(
        select(Contact.id, Contact.full_name)
    ).all()

    created = 0

    for contact_id, full_name in contacts:
        exists = db.execute(
            select(Message.id).where(
                Message.campaign_id == campaign_id,
                Message.contact_id == contact_id
            )
        ).first()

        if exists:
            continue

        subject = tpl_subject.replace("{name}", full_name or "")
        body = tpl_body.replace("{name}", full_name or "")

        m = Message(
            campaign_id=campaign_id,
            contact_id=contact_id,
            subject=subject,
            body=body,
            status="queued",
        )
        db.add(m)
        created += 1

    db.commit()
    return created


def send_campaign_job(db: Session, campaign_id: int) -> dict:
    db.execute(
        text("UPDATE campaigns SET status='sending' WHERE id=:id"),
        {"id": campaign_id}
    )
    db.commit()

    per_minute = max(1, settings.RATE_LIMIT_PER_MINUTE)
    delay = 60.0 / per_minute

    q = select(Message).where(Message.campaign_id == campaign_id)
    messages = db.scalars(q).all()

    for m in messages:
        if m.status in ("sent", "skipped"):
            continue

        if _is_unsubscribed(db, m.contact_id):
            m.status = "skipped"
            m.last_error = "Unsubscribed"
            db.add(SendLog(
                message_id=m.id,
                status="failed",
                smtp_reply="Unsubscribed"
            ))
            db.commit()
            continue

        contact = db.get(Contact, m.contact_id)
        if not contact or not contact.consent:
            m.status = "skipped"
            m.last_error = "No consent"
            db.add(SendLog(
                message_id=m.id,
                status="failed",
                smtp_reply="No consent"
            ))
            db.commit()
            continue

        ok, smtp_code, smtp_reply = send_email(contact.email, m.subject, m.body)
        m.attempts += 1

        if ok:
            m.status = "sent"
            m.sent_at = func.now()
            db.add(SendLog(message_id=m.id, status="sent"))
            db.commit()
        else:
            m.last_error = smtp_reply
            if m.attempts < settings.MAX_RETRY:
                m.status = "queued"
                db.add(SendLog(
                    message_id=m.id,
                    status="retry",
                    smtp_code=smtp_code,
                    smtp_reply=smtp_reply
                ))
            else:
                m.status = "failed"
                db.add(SendLog(
                    message_id=m.id,
                    status="failed",
                    smtp_code=smtp_code,
                    smtp_reply=smtp_reply
                ))
            db.commit()

        time.sleep(delay)

    db.execute(
        text("UPDATE campaigns SET status='done' WHERE id=:id"),
        {"id": campaign_id}
    )
    db.commit()

    total = db.scalar(
        select(func.count()).select_from(Message).where(Message.campaign_id == campaign_id)
    )
    sent = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.campaign_id == campaign_id,
            Message.status == "sent"
        )
    )
    failed = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.campaign_id == campaign_id,
            Message.status == "failed"
        )
    )
    skipped = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.campaign_id == campaign_id,
            Message.status == "skipped"
        )
    )

    return {
        "campaign_id": campaign_id,
        "total": total or 0,
        "sent": sent or 0,
        "failed": failed or 0,
        "skipped": skipped or 0,
    }