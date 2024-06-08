from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import TelegramUser


# @receiver(post_save, sender=TelegramUser)
# def process_referral(sender, instance, created, **kwargs):
#     if created:
#         if not instance.referral_code:
#             instance.referral_code = generate_unique_referral_code()
#
#         instance.save()
