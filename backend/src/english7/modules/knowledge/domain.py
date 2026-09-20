from enum import StrEnum


class ConceptType(StrEnum):
    GRAMMAR = "grammar"
    VOCABULARY_SENSE = "vocabulary_sense"
    PRONUNCIATION_FEATURE = "pronunciation_feature"
    TOPIC = "topic"
    SKILL = "skill"


class AssertionType(StrEnum):
    TEACHES = "teaches"
    PRACTICES = "practices"
    EXPLAINS = "explains"
    INTRODUCES = "introduces"
    REVIEWS = "reviews"
    PREREQUISITE_OF = "prerequisite_of"
    HAS_COMMON_MISTAKE = "has_common_mistake"


class GraphBuildStatus(StrEnum):
    BUILDING = "building"
    VALIDATED = "validated"
    ACTIVE = "active"
    FAILED = "failed"
    RETIRED = "retired"
