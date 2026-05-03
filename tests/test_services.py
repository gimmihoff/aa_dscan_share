import unittest


try:
    import django
    from django.conf import settings
    from django.core.management import call_command
    from django.test import TestCase
except ImportError:
    django = None
    settings = None
    TestCase = unittest.TestCase


@unittest.skipIf(django is None, "Django is required for D-scan share service tests")
class DScanShareServiceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure(
                DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
                INSTALLED_APPS=["aa_core_hub", "aa_dscan_share"],
                SECRET_KEY="test",
                USE_TZ=True,
                DATABASES={
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": ":memory:",
                    },
                },
            )
        django.setup()
        call_command("migrate", "aa_core_hub", verbosity=0)
        super().setUpClass()

    def test_detected_structures_are_saved_to_core(self):
        from aa_core_hub.api import create_dscan
        from aa_dscan_share.services import save_detected_structures

        dscan = create_dscan(
            raw_text="Astrahus\tUpwell Structure\t1,000 km\nProbe\tCombat Scanner Probe\t2 AU",
            solar_system_id=30000142,
            solar_system_name="Jita",
        )

        saved = save_detected_structures(
            dscan=dscan,
            structures=[
                {
                    "name": "Astrahus",
                    "type_name": "Upwell Structure",
                    "standing": "HOSTILE",
                }
            ],
        )

        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].standing, "HOSTILE")
        self.assertEqual(saved[0].solar_system_id, 30000142)

    def test_fleet_composition_groups_non_structure_items(self):
        from aa_core_hub.api import create_dscan
        from aa_dscan_share.services import get_fleet_composition

        dscan = create_dscan(
            raw_text=(
                "Pilot One\tCaracal\t1 AU\n"
                "Pilot Two\tCaracal\t1 AU\n"
                "Pilot Three\tScythe\t1 AU\n"
                "Astrahus\tUpwell Structure\t1,000 km"
            ),
            solar_system_id=30000142,
            solar_system_name="Jita",
        )

        composition = get_fleet_composition(dscan)

        self.assertEqual(composition[0]["type_name"], "Caracal")
        self.assertEqual(composition[0]["count"], 2)
        self.assertEqual(composition[1]["type_name"], "Scythe")
        self.assertEqual(composition[1]["count"], 1)

    def test_structure_rows_separate_upwell_structures_from_fleet(self):
        from aa_core_hub.api import create_dscan
        from aa_dscan_share.services import get_fleet_composition, get_structure_rows

        dscan = create_dscan(
            raw_text=(
                "Pilot One\tCaracal\t1 AU\n"
                "1035466617946\tUpwell Structure\t1,000 km\n"
                "Jita IV - Moon 4\tCustoms Office\t2 AU\n"
                "Jita\tStargate\t5 AU"
            ),
            solar_system_id=30000142,
            solar_system_name="Jita",
        )

        composition = get_fleet_composition(dscan)
        structures = get_structure_rows(dscan)

        self.assertEqual(len(composition), 1)
        self.assertEqual(composition[0]["type_name"], "Caracal")
        self.assertEqual(len(structures), 3)
