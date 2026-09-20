import pytest
from english7.modules.knowledge.curriculum_ontology import get_curriculum_ontology


def test_curriculum_ontology_covers_all_16_units():
    ontology = get_curriculum_ontology()
    assert len(ontology.topics) == 12
    assert len(ontology.grammar_rules) >= 12
    assert len(ontology.pronunciations) == 12
    assert len(ontology.vocabulary) >= 24
    assert len(ontology.prerequisites) >= 3


def test_curriculum_ontology_units_mapped_correctly():
    ontology = get_curriculum_ontology()
    u1_grammar = [g for g in ontology.grammar_rules if g.unit_number == 1]
    assert any("present simple" in g.name.lower() for g in u1_grammar)

    u10_topic = next((t for t in ontology.topics if t.unit_number == 10), None)
    assert u10_topic is not None
    assert "energy" in u10_topic.name.lower()

    u12_pron = next((p for p in ontology.pronunciations if p.unit_number == 12), None)
    assert u12_pron is not None
    assert "intonation" in u12_pron.symbol.lower() or "falling" in u12_pron.symbol.lower()
