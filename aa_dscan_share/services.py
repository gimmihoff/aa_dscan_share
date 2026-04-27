from aa_core_hub.api import DScanItem, Structure, create_or_update_structure, parse_dscan

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


def get_detected_structure_rows(*, raw_text: str, solar_system_id: int):
    rows = []
    for index, item in enumerate(parse_dscan(raw_text)):
        if item.get("category") not in STRUCTURE_CATEGORIES:
            continue
        known_structure = find_known_structure_from_values(
            name=item["name"],
            solar_system_id=solar_system_id,
        )
        rows.append(
            {
                "index": index,
                "name": item["name"],
                "type_name": item["type_name"],
                "distance": item["distance"],
                "category": item.get("category", ""),
                "known_structure": known_structure,
            }
        )
    return rows


def find_known_structure_from_values(*, name: str, solar_system_id: int):
    return (
        Structure.objects.filter(
            solar_system_id=solar_system_id,
            name__iexact=name,
        )
        .order_by("-updated_at")
        .first()
    )


def save_detected_structures(
    *,
    dscan,
    structures,
):
    saved = []
    for item in structures:
        structure = create_or_update_structure(
            name=item["name"],
            standing=item["standing"],
            type_name=item.get("type_name", ""),
            owner_alliance_id=item.get("owner_alliance_id"),
            owner_corporation_id=item.get("owner_corporation_id"),
            solar_system_id=dscan.solar_system_id,
            solar_system_name=dscan.solar_system_name,
            source="DSCAN_SHARE",
            notes=item.get("notes", ""),
        )
        saved.append(structure)
    return saved
