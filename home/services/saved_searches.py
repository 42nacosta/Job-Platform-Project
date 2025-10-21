from django.db.models import Q
from django.utils import timezone
from accounts.models import Profile
from django.contrib.auth.models import User
from home.models import SavedCandidateSearch, SavedCandidateMatch

def _profile_queryset_for_search(s: SavedCandidateSearch):
    base = Profile.objects.select_related("user").filter(
        user__is_active=True,
        is_recruiter=False,
    ).exclude(visibility="PRIVATE")
    q = Q()

    if s.keywords:
        kw = s.keywords.strip()
        q &= (
            Q(headline__icontains=kw) |
            Q(skills__icontains=kw) |
            Q(projects__icontains=kw) |
            Q(experience__icontains=kw) |
            Q(education__icontains=kw)
        )

    if s.location:
        q &= Q(location__icontains=s.location)

    if s.min_years_experience:
        q &= Q(experience__icontains=f"{s.min_years_experience}+")

    return base.filter(q)

def run_search_and_record_new_matches(s: SavedCandidateSearch) -> int:
    qs = _profile_queryset_for_search(s)
    count_new = 0
    for prof in qs:
        if prof.user_id == s.owner_id:
            continue
        obj, created = SavedCandidateMatch.objects.get_or_create(search=s, candidate=prof.user)
        if created:
            count_new += 1
    s.last_run_at = timezone.now()
    s.save(update_fields=["last_run_at"])
    return count_new
