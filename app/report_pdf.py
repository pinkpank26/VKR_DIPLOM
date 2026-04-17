import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import Campaign, Message, Contact


def _register_font():
    possible_fonts = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("AppFont", font_path))
            return "AppFont"

    return "Helvetica"


def build_campaign_report_pdf(db: Session, campaign_id: int) -> str:
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError("Кампания не найдена")

    total = db.scalar(
        select(func.count()).select_from(Message).where(Message.campaign_id == campaign_id)
    ) or 0

    sent = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.campaign_id == campaign_id,
            Message.status == "sent",
        )
    ) or 0

    failed = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.campaign_id == campaign_id,
            Message.status == "failed",
        )
    ) or 0

    skipped = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.campaign_id == campaign_id,
            Message.status == "skipped",
        )
    ) or 0

    rows = db.execute(
        select(
            Message.id,
            Contact.email,
            Contact.full_name,
            Message.status,
            Message.attempts,
            Message.last_error,
            Message.sent_at,
        )
        .join(Contact, Contact.id == Message.contact_id)
        .where(Message.campaign_id == campaign_id)
        .order_by(Message.id.asc())
    ).all()

    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"campaign_{campaign_id}_report.pdf"
    filepath = os.path.join(reports_dir, filename)

    pdf = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    font_name = _register_font()

    y = height - 40

    def write_line(text: str, size: int = 11, gap: int = 16):
        nonlocal y
        if y < 50:
            pdf.showPage()
            pdf.setFont(font_name, 11)
            y = height - 40
        pdf.setFont(font_name, size)
        pdf.drawString(40, y, text)
        y -= gap

    write_line("Отчет по кампании массовой рассылки", 14, 24)
    write_line(f"Кампания ID: {campaign.id}")
    write_line(f"Название: {campaign.name}")
    write_line(f"Описание: {campaign.description or '-'}")
    write_line(f"Статус: {campaign.status}")
    write_line(f"Дата формирования отчета: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    write_line("")
    write_line("Сводная информация", 12, 20)
    write_line(f"Всего сообщений: {total}")
    write_line(f"Успешно отправлено: {sent}")
    write_line(f"Ошибок отправки: {failed}")
    write_line(f"Пропущено: {skipped}")
    write_line("")
    write_line("Детализация сообщений", 12, 20)

    for row in rows:
        msg_id, email, full_name, status, attempts, last_error, sent_at = row
        sent_at_str = sent_at.strftime("%d.%m.%Y %H:%M:%S") if sent_at else "-"
        err = (last_error or "-").replace("\n", " ")
        line1 = f"Сообщение #{msg_id} | {email} | {full_name or '-'}"
        line2 = f"Статус: {status} | Попытки: {attempts} | Отправлено: {sent_at_str}"
        line3 = f"Ошибка: {err}"

        write_line(line1)
        write_line(line2)
        write_line(line3)
        write_line("-" * 80)

    pdf.save()
    return filepath