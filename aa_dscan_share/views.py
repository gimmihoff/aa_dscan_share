from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse

from aa_core_hub.api import create_dscan, get_dscan_by_public_id

from .forms import DetectedStructureForm, DScanSubmitForm
from .services import (
    annotate_dscan_items,
    get_detected_structure_rows,
    get_fleet_composition,
    get_system_timeline,
    save_detected_structures,
)


@login_required
@permission_required("aa_core_hub.add_dscan", raise_exception=True)
def submit_dscan(request):
    detected_rows = []
    structure_forms = []
    structure_form_rows = []
    if request.method == "POST":
        form = DScanSubmitForm(request.POST)
        if form.is_valid():
            detected_rows = get_detected_structure_rows(
                raw_text=form.cleaned_data["raw_text"],
                solar_system_id=form.cleaned_data["solar_system_id"],
            )
            if request.POST.get("action") == "preview":
                structure_forms = [
                    DetectedStructureForm(
                        initial={
                            "save": True,
                            "name": row["name"],
                            "type_name": row["type_name"],
                            "distance": row["distance"],
                            "category": row["category"],
                            "standing": row["known_structure"].standing
                            if row["known_structure"]
                            else "HOSTILE",
                            "owner_alliance_id": row["known_structure"].owner_alliance_id
                            if row["known_structure"]
                            else None,
                            "owner_corporation_id": row["known_structure"].owner_corporation_id
                            if row["known_structure"]
                            else None,
                        },
                        prefix=f"structure-{row['index']}",
                    )
                    for row in detected_rows
                ]
                structure_form_rows = zip(detected_rows, structure_forms)
            else:
                selected_structures = []
                for row in detected_rows:
                    structure_form = DetectedStructureForm(
                        request.POST,
                        prefix=f"structure-{row['index']}",
                    )
                    if structure_form.is_valid() and structure_form.cleaned_data["save"]:
                        selected_structures.append(structure_form.cleaned_data)

                dscan = create_dscan(
                    raw_text=form.cleaned_data["raw_text"],
                    solar_system_id=form.cleaned_data["solar_system_id"],
                    solar_system_name=form.cleaned_data["solar_system_name"],
                    source="DSCAN_SHARE",
                    created_by_user_id=request.user.id,
                )
                saved = save_detected_structures(dscan=dscan, structures=selected_structures)
                saved_count = len(saved)
                messages.success(
                    request,
                    f"D-scan shared. Saved {saved_count} detected structure(s) to Core.",
                )
                return redirect("aa_dscan_share:view", public_id=dscan.public_id)
    else:
        form = DScanSubmitForm()

    return render(
        request,
        "aa_dscan_share/submit.html",
        {
            "form": form,
            "detected_rows": detected_rows,
            "structure_forms": structure_forms,
            "structure_form_rows": structure_form_rows,
        },
    )


@login_required
@permission_required("aa_core_hub.view_dscan", raise_exception=True)
def view_dscan(request, public_id):
    dscan = get_dscan_by_public_id(public_id)
    share_path = reverse("aa_dscan_share:view", kwargs={"public_id": dscan.public_id})
    share_url = request.build_absolute_uri(share_path)
    return render(
        request,
        "aa_dscan_share/view.html",
        {
            "dscan": dscan,
            "fleet_composition": get_fleet_composition(dscan),
            "rows": annotate_dscan_items(dscan),
            "share_url": share_url,
        },
    )


@login_required
@permission_required("aa_core_hub.view_dscan", raise_exception=True)
def system_timeline(request, solar_system_id):
    timeline = get_system_timeline(solar_system_id=solar_system_id)
    system_name = timeline[0]["dscan"].solar_system_name if timeline else ""
    return render(
        request,
        "aa_dscan_share/timeline.html",
        {
            "solar_system_id": solar_system_id,
            "system_name": system_name,
            "timeline": timeline,
        },
    )
