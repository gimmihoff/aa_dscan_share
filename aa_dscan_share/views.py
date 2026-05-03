from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from aa_core_hub.api import (
    EveSolarSystem,
    Structure,
    StructureTimer,
    create_dscan,
    get_dscan_by_public_id,
)

from .forms import DetectedStructureForm, DScanSubmitForm, StructureDataForm
from .services import (
    annotate_dscan_items,
    get_detected_structure_rows,
    get_fleet_composition,
    get_recent_systems_for_user,
    get_structure_rows,
    get_system_suggestions,
    get_system_timeline,
    save_detected_structures,
)


@login_required
@permission_required("aa_core_hub.add_dscan", raise_exception=True)
def submit_dscan(request):
    detected_rows = []
    structure_forms = []
    structure_form_rows = []
    recent_systems = get_recent_systems_for_user(user_id=request.user.id)
    system_suggestions = get_system_suggestions()
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
            "recent_systems": recent_systems,
            "system_suggestions": system_suggestions,
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
            "structure_rows": get_structure_rows(dscan),
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


@login_required
@permission_required("aa_core_hub.change_structure", raise_exception=True)
def structure_data(request, solar_system_id):
    structure_qs = Structure.objects.filter(solar_system_id=solar_system_id).order_by(
        "standing",
        "type_name",
        "name",
    )
    system = EveSolarSystem.objects.filter(solar_system_id=solar_system_id).first()
    system_name = (
        system.name
        if system
        else structure_qs.first().solar_system_name
        if structure_qs.exists()
        else ""
    )

    if request.method == "POST":
        structure = get_object_or_404(
            Structure,
            pk=request.POST.get("structure_pk"),
            solar_system_id=solar_system_id,
        )
        form = StructureDataForm(
            request.POST,
            instance=structure,
            prefix=f"structure-{structure.pk}",
        )
        if form.is_valid():
            structure = form.save()
            if form.cleaned_data.get("timer_occurs_at"):
                StructureTimer.objects.create(
                    structure=structure,
                    phase=form.cleaned_data.get("timer_phase") or "OTHER",
                    occurs_at=form.cleaned_data["timer_occurs_at"],
                    is_confirmed=form.cleaned_data.get("timer_confirmed") or False,
                    notes=form.cleaned_data.get("timer_notes") or "",
                )
                if structure.status not in ("DESTROYED", "REMOVED"):
                    structure.status = "REINFORCED"
                    structure.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Updated structure data for {structure.name}.")
            return redirect("aa_dscan_share:structure_data", solar_system_id=solar_system_id)
        messages.error(request, "Structure data could not be saved. Check the highlighted fields.")
    else:
        form = None

    structures = list(structure_qs.prefetch_related("timers"))
    structure_rows = []
    for structure in structures:
        structure_rows.append(
            {
                "structure": structure,
                "form": form
                if form is not None and form.instance.pk == structure.pk
                else StructureDataForm(instance=structure, prefix=f"structure-{structure.pk}"),
                "next_timer": structure.timers.order_by("occurs_at").first(),
            }
        )

    return render(
        request,
        "aa_dscan_share/structure_data.html",
        {
            "solar_system_id": solar_system_id,
            "system_name": system_name,
            "structure_rows": structure_rows,
        },
    )


@login_required
@permission_required("aa_core_hub.view_dscan", raise_exception=True)
def system_search(request):
    query = request.GET.get("q", "")
    systems = get_system_suggestions(query=query, limit=20)
    return JsonResponse(
        {
            "results": [
                {
                    "solar_system_id": system.solar_system_id,
                    "name": system.name,
                }
                for system in systems
            ]
        }
    )
