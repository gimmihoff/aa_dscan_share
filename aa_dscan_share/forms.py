from django import forms
from django.core.exceptions import ValidationError

from aa_core_hub.api import EveSolarSystem


STANDING_CHOICES = (
    ("HOSTILE", "Hostile"),
    ("NEUTRAL", "Neutral"),
    ("FRIENDLY", "Friendly"),
)


class DScanSubmitForm(forms.Form):
    system = forms.CharField(label="System", max_length=128)
    solar_system_id = forms.IntegerField(widget=forms.HiddenInput, required=False, min_value=1)
    raw_text = forms.CharField(label="D-scan", widget=forms.Textarea(attrs={"rows": 14}))

    def clean(self):
        cleaned_data = super().clean()
        system = (cleaned_data.get("system") or "").strip()
        solar_system_id = cleaned_data.get("solar_system_id")

        eve_system = None
        if solar_system_id:
            eve_system = EveSolarSystem.objects.filter(solar_system_id=solar_system_id).first()
        if not eve_system and system:
            eve_system = EveSolarSystem.objects.filter(name__iexact=system).first()
        if not eve_system and system.isdigit():
            eve_system = EveSolarSystem.objects.filter(solar_system_id=int(system)).first()
        if not eve_system:
            raise ValidationError("Select a system from Core's geography cache before submitting.")

        cleaned_data["solar_system_id"] = eve_system.solar_system_id
        cleaned_data["solar_system_name"] = eve_system.name
        cleaned_data["system"] = eve_system.name
        return cleaned_data


class DetectedStructureForm(forms.Form):
    save = forms.BooleanField(required=False, initial=True)
    name = forms.CharField(widget=forms.HiddenInput)
    type_name = forms.CharField(required=False, widget=forms.HiddenInput)
    distance = forms.CharField(required=False, widget=forms.HiddenInput)
    category = forms.CharField(required=False, widget=forms.HiddenInput)
    standing = forms.ChoiceField(choices=STANDING_CHOICES, initial="HOSTILE")
    owner_alliance_id = forms.IntegerField(required=False, min_value=1)
    owner_corporation_id = forms.IntegerField(required=False, min_value=1)
    notes = forms.CharField(required=False, widget=forms.TextInput)
