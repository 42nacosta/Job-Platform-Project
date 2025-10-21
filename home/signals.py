from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Profile
from home.models import SavedCandidateSearch
from home.services.saved_searches import run_search_and_record_new_matches

@receiver(post_save, sender=Profile)
def reindex_saved_searches_on_profile_change(sender, instance: Profile, **kwargs):
    if instance.is_recruiter:
        return
    active = SavedCandidateSearch.objects.select_related("owner").filter(is_active=True)
    for s in active:
        run_search_and_record_new_matches(s)