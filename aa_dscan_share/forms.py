from django import forms


class DScanSubmitForm(forms.Form):
    solar_system_id = forms.IntegerField(label="System ID", min_value=1)
    solar_system_name = forms.CharField(label="System name", max_length=128, required=False)
    raw_text = forms.CharField(label="D-scan", widget=forms.Textarea(attrs={"rows": 14}))
    save_detected_structures = forms.BooleanField(
        label="Save detected structures to Core",
        required=False,
        initial=True,
    )
    structure_standing = forms.ChoiceField(
        label="Standing for saved structures",
        choices=(
            ("HOSTILE", "Hostile"),
            ("NEUTRAL", "Neutral"),
            ("FRIENDLY", "Friendly"),
        ),
        initial="HOSTILE",
    )
    owner_alliance_id = forms.IntegerField(label="Owner alliance ID", required=False, min_value=1)
    owner_corporation_id = forms.IntegerField(label="Owner corporation ID", required=False, min_value=1)
    notes = forms.CharField(label="Structure notes", required=False, widget=forms.Textarea(attrs={"rows": 3}))

