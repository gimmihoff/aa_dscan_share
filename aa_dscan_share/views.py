from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse

from aa_core_hub.api import create_dscan, get_dscan_by_public_id

from .forms import DScanSubmitForm
from .services import annotate_dscan_items, save_detected_structures


@login_required
@permission_required("aa_core_hub.add_dscan", raise_exception=True)
def submit_dscan(request):
    if request.method == "POST":
        form = DScanSubmitForm(request.POST)
        if form.is_valid():
            dscan = create_dscan(
                raw_text=form.cleaned_data["raw_text"],
                solar_system_id=form.cleaned_data["solar_system_id"],
                solar_system_name=form.cleaned_data["solar_system_name"],
                source="DSCAN_SHARE",
                created_by_user_id=request.user.id,
            )
            saved_count = 0
            if form.cleaned_data["save_detected_structures"]:
                saved = save_detected_structures(
                    dscan=dscan,
                    standing=form.cleaned_data["structure_standing"],
                    owner_alliance_id=form.cleaned_data["owner_alliance_id"],
                    owner_corporation_id=form.cleaned_data["owner_corporation_id"],
                    notes=form.cleaned_data["notes"],
                )
                saved_count = len(saved)
            messages.success(
                request,
                f"D-scan shared. Saved {saved_count} detected structure(s) to Core.",
            )
            return redirect("aa_dscan_share:view", public_id=dscan.public_id)
    else:
        form = DScanSubmitForm()

    return render(request, "aa_dscan_share/submit.html", {"form": form})


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
            "rows": annotate_dscan_items(dscan),
            "share_url": share_url,
        },
    )

