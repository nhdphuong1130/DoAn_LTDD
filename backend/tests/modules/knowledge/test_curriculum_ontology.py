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


def test_curriculum_ontology_comprehensive_vocabulary_all_units():
    ontology = get_curriculum_ontology()
    assert len(ontology.vocabulary) == 300
    for unit_number in range(1, 13):
        unit_vocab = [v for v in ontology.vocabulary if v.unit_number == unit_number]
        assert len(unit_vocab) == 25, f"Unit {unit_number} has {len(unit_vocab)} words, expected 25"
        for v in unit_vocab:
            assert v.word.strip() != ""
            assert v.pos in {"noun", "verb", "adj"}
            assert v.ipa.startswith("/") and v.ipa.endswith("/")
            assert v.meaning_vi.strip() != ""
            assert v.example.strip() != ""

