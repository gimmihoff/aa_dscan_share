from aa_core_hub.api import DScanItem, Structure, create_or_update_structure

STRUCTURE_CATEGORIES = {
    "STRUCTURE",
    "SOV",
    "FLEX",
    "CUSTOMS_OFFICE",
    "SKYHOOK",
    "MOON_DRILL",
    "MERCENARY_DEN",
}


def is_structure_item(item: DScanItem) -> bool:
    return item.category in STRUCTURE_CATEGORIES


def find_known_structure(*, item: DScanItem, solar_system_id: int):
    return (
        Structure.objects.filter(
            solar_system_id=solar_system_id,
            name__iexact=item.name,
        )
        .order_by("-updated_at")
        .first()
    )


def annotate_dscan_items(dscan):
    rows = []
    for item in dscan.items.all().order_by("category", "type_name", "name"):
        known_structure = None
        if is_structure_item(item):
            known_structure = find_known_structure(
                item=item,
                solar_system_id=dscan.solar_system_id,
            )
        rows.append(
            {
                "item": item,
                "is_structure": is_structure_item(item),
                "known_structure": known_structure,
            }
        )
    return rows


def save_detected_structures(
    *,
    dscan,
    standing: str,
    owner_alliance_id: int | None = None,
    owner_corporation_id: int | None = None,
    notes: str = "",
):
    saved = []
    for item in dscan.items.all():
        if not is_structure_item(item):
            continue
        structure = create_or_update_structure(
            name=item.name,
            standing=standing,
            type_name=item.type_name,
            owner_alliance_id=owner_alliance_id,
            owner_corporation_id=owner_corporation_id,
            solar_system_id=dscan.solar_system_id,
            solar_system_name=dscan.solar_system_name,
            source="DSCAN_SHARE",
            notes=notes,
        )
        saved.append(structure)
    return saved

