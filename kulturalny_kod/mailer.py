from django.core.mail import mail_admins
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def notify_admin(subject: str, message: str):
    mail_admins(subject, message)
    logger.info(f"Wysłano powiadomienie do admina: {subject}")
