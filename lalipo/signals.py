from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from allauth.socialaccount.models import SocialToken


@receiver(user_logged_out)
def cleanup(sender, user, request, **kwargs):
    """Remove tokens for user"""
    tokens = SocialToken.objects.filter(account__user=user)
    res = tokens.delete()
    print("Deleted tokens", res)
