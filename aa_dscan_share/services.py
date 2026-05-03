from aa_core_hub.api import (
    DScanItem,
    EveSolarSystem,
    Structure,
    create_or_update_structure,
    get_dscan_timeline_for_system,
    parse_dscan,
)

STRUCTURE_CATEGORIES = {
    "STRUCTURE",
    "SOV",
    "FLEX",
    "CUSTOMS_OFFICE",
    "SKYHOOK",
    "MOON_DRILL",
    "MERCENARY_DEN",
}


def get_recent_systems_for_user(*, user_id: int, limit: int = 10):
    seen = set()
    systems = []
    dscans = (
        get_dscan_recent_for_user(user_id=user_id)
        if user_id
        else []
    )
    for dscan in dscans:
        if not dscan.solar_system_id or dscan.solar_system_id in seen:
            continue
        seen.add(dscan.solar_system_id)
        systems.append(
            {
                "solar_system_id": dscan.solar_system_id,
                "solar_system_name": dscan.solar_system_name,
            }
        )
        if len(systems) >= limit:
            break
    return systems


def get_dscan_recent_for_user(*, user_id: int, limit: int = 100):
    from aa_core_hub.api import DScan

    return DScan.objects.filter(created_by_user_id=user_id).order_by("-created_at")[:limit]


def get_system_suggestions(*, query: str = "", limit: int = 25):
    qs = EveSolarSystem.objects.all().order_by("name")
    query = (query or "").strip()
    if query:
        qs = qs.filter(name__icontains=query)
    return qs[:limit]


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


def is_fleet_item(item: DScanItem) -> bool:
    return not is_structure_item(item) and item.category not in {"PROBE", "DEPLOYABLE"}


def get_fleet_composition(dscan):
    composition = {}
    for item in dscan.items.all():
        if not is_fleet_item(item):
            continue
        type_name = item.type_name or "Unknown"
        if type_name not in composition:
            composition[type_name] = {
                "type_name": type_name,
                "category": item.category,
                "count": 0,
                "names": [],
            }
        composition[type_name]["count"] += 1
        composition[type_name]["names"].append(item.name)
    return sorted(
        composition.values(),
        key=lambda row: (-row["count"], row["type_name"].lower()),
    )


def get_system_timeline(*, solar_system_id: int, limit: int = 50):
    timeline = []
    for dscan in get_dscan_timeline_for_system(solar_system_id=solar_system_id, limit=limit):
        composition = get_fleet_composition(dscan)
        timeline.append(
            {
                "dscan": dscan,
                "composition": composition,
                "ship_count": sum(row["count"] for row in composition),
                "type_count": len(composition),
            }
        )
    return timeline


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
