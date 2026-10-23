"""Fast, dependency-free tests of the project's evidence and planning contracts."""

import copy
import json
import unittest

from tools import validate_hardware, validate_roadmap
from tools.run_arm64_smoke import command
from pathlib import Path


class HardwareMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(validate_hardware.MAP_PATH.read_text(encoding="utf-8"))

    def test_reference_map_passes(self):
        self.assertEqual(validate_hardware.validate(self.reference), [])

    def test_overlapping_mmio_rejected(self):
        broken = copy.deepcopy(self.reference)
        broken["regions"][2]["base"] = broken["regions"][1]["base"]
        self.assertTrue(any("overlap" in e for e in validate_hardware.validate(broken)))

    def test_missing_provenance_rejected(self):
        broken = copy.deepcopy(self.reference)
        broken["regions"][0]["source"] = "imaginary"
        self.assertTrue(any("source" in e for e in validate_hardware.validate(broken)))

    def test_non_object_metadata_rejected(self):
        for value in (None, [], "T8103", 1):
            with self.subTest(value=value):
                self.assertTrue(validate_hardware.validate(value))

    def test_unhashable_region_fields_rejected_without_crash(self):
        for field in ("name", "source", "confidence", "status"):
            for value in ([], {}):
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken["regions"][1][field] = value
                    self.assertTrue(validate_hardware.validate(broken))

    def test_invalid_ram_extent_rejected(self):
        for size in ("0x0", "0x10000000000000000"):
            with self.subTest(size=size):
                broken = copy.deepcopy(self.reference)
                broken["regions"][0]["size"] = size
                self.assertTrue(validate_hardware.validate(broken))


class RoadmapTests(unittest.TestCase):
    def test_exactly_365_phases_with_checks(self):
        self.assertEqual(validate_roadmap.validate(validate_roadmap.ROADMAP.read_text(encoding="utf-8")), [])

    def test_duplicate_phase_rejected(self):
        text = validate_roadmap.ROADMAP.read_text(encoding="utf-8")
        text = text.replace("P365", "P364")
        self.assertTrue(validate_roadmap.validate(text))


class SmokeCommandTests(unittest.TestCase):
    def test_machine_is_explicitly_generic_virt(self):
        argv = command("qemu-system-aarch64", Path("guest.elf"))
        self.assertEqual(argv[argv.index("-M") + 1], "virt")
        self.assertIn("-kernel", argv)


if __name__ == "__main__":
    unittest.main()
