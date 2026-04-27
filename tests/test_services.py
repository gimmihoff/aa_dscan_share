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

        saved = save_detected_structures(dscan=dscan, standing="HOSTILE")

        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].standing, "HOSTILE")
        self.assertEqual(saved[0].solar_system_id, 30000142)

