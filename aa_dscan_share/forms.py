from django import forms


STANDING_CHOICES = (
    ("HOSTILE", "Hostile"),
    ("NEUTRAL", "Neutral"),
    ("FRIENDLY", "Friendly"),
)


class DScanSubmitForm(forms.Form):
    solar_system_id = forms.IntegerField(label="System ID", min_value=1)
    solar_system_name = forms.CharField(label="System name", max_length=128, required=False)
    raw_text = forms.CharField(label="D-scan", widget=forms.Textarea(attrs={"rows": 14}))


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
