from django import forms
from home.models import SavedCandidateSearch

class SavedCandidateSearchForm(forms.ModelForm):
    class Meta:
        model = SavedCandidateSearch
        fields = ["name", "keywords", "location", "min_years_experience", "is_active"]
