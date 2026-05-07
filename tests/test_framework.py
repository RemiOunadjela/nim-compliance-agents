"""Tests for framework loading."""

from __future__ import annotations

import pytest

from nim_compliance_agents.frameworks.loader import list_frameworks, load_framework


class TestFrameworkLoader:
    def test_load_dsa(self):
        fw = load_framework("dsa")
        assert fw.name == "Digital Services Act"
        assert fw.abbreviation == "DSA"
        assert fw.jurisdiction == "European Union"

    def test_dsa_has_categories(self):
        fw = load_framework("dsa")
        assert len(fw.violation_categories) >= 6
        ids = {c.id for c in fw.violation_categories}
        assert "hate_speech" in ids
        assert "illegal_content" in ids
        assert "minor_safety" in ids

    def test_dsa_severity_scale(self):
        fw = load_framework("dsa")
        assert "p0" in fw.severity_scale
        assert "p4" in fw.severity_scale

    def test_missing_framework_raises(self):
        with pytest.raises(FileNotFoundError):
            load_framework("nonexistent_framework")

    def test_list_frameworks(self):
        available = list_frameworks()
        assert "dsa" in available

    def test_load_osa(self):
        fw = load_framework("osa")
        assert fw.name == "Online Safety Act"
        assert fw.abbreviation == "OSA"
        assert fw.jurisdiction == "United Kingdom"

    def test_osa_has_categories(self):
        fw = load_framework("osa")
        assert len(fw.violation_categories) >= 6
        ids = {c.id for c in fw.violation_categories}
        assert "child_sexual_abuse_material" in ids
        assert "terrorism_content" in ids
        assert "harm_to_children" in ids
        assert "fraud_and_scams" in ids

    def test_osa_severity_scale(self):
        fw = load_framework("osa")
        assert "p0" in fw.severity_scale
        assert "p4" in fw.severity_scale

    def test_osa_in_list(self):
        available = list_frameworks()
        assert "osa" in available
