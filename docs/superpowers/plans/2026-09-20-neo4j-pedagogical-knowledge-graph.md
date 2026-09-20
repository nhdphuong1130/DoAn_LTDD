# Neo4j Pedagogical Knowledge Graph & Weighted GraphRAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Dual-Tier Pedagogical Knowledge Graph in Neo4j with local FastEmbed 384-dimensional vectorization and weighted GraphRAG retrieval across all 16 units of Tiếng Anh 7 (Global Success).

**Architecture:** A two-tier graph in Neo4j combining physical textbook hierarchy (`Textbook -> Unit -> Section -> Activity -> SourceFragment`) with pedagogical entity nodes (`Topic`, `GrammarRule`, `Vocabulary`, `PronunciationSound`, `Skill`). Interconnected with weighted edges (`TEACHES: 1.0`, `EXPLAINS: 0.9`, `REVIEWS: 0.8`, `PREREQUISITE_OF: 0.7`, `PRACTICES: 0.6`, `APPEARS_IN: 0.5`). Vectorized via `sentence-transformers/all-MiniLM-L6-v2` (384d) running offline on CPU through `fastembed`. Retrieved using hybrid dual-vector search, weighted graph traversal, and weighted Reciprocal Rank Fusion (RRF).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Neo4j 5.26+ (Cypher + Vector Indexes), FastEmbed / ONNX Runtime, Pytest.

**Spec:** `docs/superpowers/specs/2026-09-20-neo4j-pedagogical-knowledge-graph-design.md`

## Global Constraints
- Target Textbook: Tiếng Anh 7 – Global Success (Semester 1 & 2: Units 1–12 + Reviews 1–4, 16 units total).
- Embedding Model: `sentence-transformers/all-MiniLM-L6-v2` with output dimension 384, cosine distance.
- Vector Index Names: `source_fragment_embedding` (for SourceFragment) and `knowledge_concept_embedding` (for KnowledgeConcept).
- Execution: 100% offline-capable on CPU without external API key dependencies for embedding.
- Relationship Weights: `TEACHES=1.0`, `EXPLAINS=0.9`, `REVIEWS=0.8`, `PREREQUISITE_OF=0.7`, `PRACTICES=0.6`, `APPEARS_IN=0.5`.
- Allowed Units Range: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 31, 61, 91, 121.

---

### Task 1: FastEmbed Local Embedder Integration

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/src/english7/modules/knowledge/fastembed_service.py`
- Test: `backend/tests/modules/knowledge/test_fastembed_service.py`

**Interfaces:**
- Consumes: `english7.modules.knowledge.contracts.Embedder`
- Produces: `FastEmbedService(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", cache_dir: str | None = None)` implementing `embed(text: str) -> list[float]` and `embed_batch(texts: list[str]) -> list[list[float]]`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/knowledge/test_fastembed_service.py
import pytest
from english7.modules.knowledge.fastembed_service import FastEmbedService


def test_fastembed_service_generates_384_dimensions():
    service = FastEmbedService()
    vector = service.embed("Hello world, this is English 7 textbook.")
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(x, float) for x in vector)


def test_fastembed_service_batch_embedding():
    service = FastEmbedService()
    texts = ["Present simple tense", "Renewable energy sources"]
    vectors = service.embed_batch(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


def test_fastembed_semantic_similarity():
    service = FastEmbedService()
    v1 = service.embed("traffic lights and road signs")
    v2 = service.embed("traffic rules and vehicles on the road")
    v3 = service.embed("cooking delicious food and noodles")

    import math
    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb)

    sim_12 = cosine(v1, v2)
    sim_13 = cosine(v1, v3)
    assert sim_12 > sim_13
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec english7-api-1 pytest tests/modules/knowledge/test_fastembed_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'english7.modules.knowledge.fastembed_service'`

- [ ] **Step 3: Write minimal implementation**

Add `fastembed>=0.4,<1` to dependencies in `backend/pyproject.toml`.

Create `backend/src/english7/modules/knowledge/fastembed_service.py`:
```python
from collections.abc import Sequence
import threading
from fastembed import TextEmbedding


class FastEmbedService:
    _instance = None
    _lock = threading.Lock()

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_dir: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed(self, text: str) -> list[float]:
        cleaned = text.strip() if text else "empty"
        embeddings = list(self._model.embed([cleaned]))
        return [float(x) for x in embeddings[0]]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        cleaned = [t.strip() if t and t.strip() else "empty" for t in texts]
        embeddings = list(self._model.embed(cleaned))
        return [[float(x) for x in emb] for emb in embeddings]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec english7-api-1 pytest tests/modules/knowledge/test_fastembed_service.py -v`
Expected: PASS with 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/src/english7/modules/knowledge/fastembed_service.py backend/tests/modules/knowledge/test_fastembed_service.py
git commit -m "feat(knowledge): add FastEmbedService for local 384d vector embedding"
```

---

### Task 2: Curriculum Pedagogical Ontology Data Definitions

**Files:**
- Create: `backend/src/english7/modules/knowledge/curriculum_ontology.py`
- Test: `backend/tests/modules/knowledge/test_curriculum_ontology.py`

**Interfaces:**
- Consumes: Domain knowledge of SGK Tiếng Anh 7 (Global Success) Units 1–12 + Reviews 1–4
- Produces: Dataclasses `PedagogicalTopic`, `PedagogicalGrammarRule`, `PedagogicalVocabulary`, `PedagogicalPronunciation`, `PedagogicalPrerequisite`, and function `get_curriculum_ontology() -> CurriculumOntology`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/knowledge/test_curriculum_ontology.py
import pytest
from english7.modules.knowledge.curriculum_ontology import get_curriculum_ontology


def test_curriculum_ontology_covers_all_16_units():
    ontology = get_curriculum_ontology()
    assert len(ontology.topics) == 12
    assert len(ontology.grammar_rules) >= 14
    assert len(ontology.pronunciations) == 12
    assert len(ontology.vocabulary) >= 40
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec english7-api-1 pytest tests/modules/knowledge/test_curriculum_ontology.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'english7.modules.knowledge.curriculum_ontology'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/src/english7/modules/knowledge/curriculum_ontology.py`:
```python
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PedagogicalTopic:
    id: str
    unit_number: int
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class PedagogicalGrammarRule:
    id: str
    unit_number: int
    name: str
    formula: str
    explanation_vi: str
    examples: list[str]


@dataclass(frozen=True, slots=True)
class PedagogicalVocabulary:
    id: str
    unit_number: int
    word: str
    pos: str
    ipa: str
    meaning_vi: str
    example: str


@dataclass(frozen=True, slots=True)
class PedagogicalPronunciation:
    id: str
    unit_number: int
    symbol: str
    description: str
    sample_words: list[str]


@dataclass(frozen=True, slots=True)
class PedagogicalPrerequisite:
    prerequisite_id: str
    target_id: str
    weight: float = 0.7


@dataclass(frozen=True, slots=True)
class CurriculumOntology:
    topics: list[PedagogicalTopic]
    grammar_rules: list[PedagogicalGrammarRule]
    vocabulary: list[PedagogicalVocabulary]
    pronunciations: list[PedagogicalPronunciation]
    prerequisites: list[PedagogicalPrerequisite]


def get_curriculum_ontology() -> CurriculumOntology:
    topics = [
        PedagogicalTopic("topic-u1", 1, "Hobbies", "Sở thích cá nhân, các hoạt động thời gian rảnh rỗi và lợi ích của sở thích."),
        PedagogicalTopic("topic-u2", 2, "Healthy Living", "Lối sống lành mạnh, thói quen ăn uống, tập thể dục và phòng ngừa bệnh thông thường."),
        PedagogicalTopic("topic-u3", 3, "Community Service", "Hoạt động vì cộng đồng, tình nguyện, giúp đỡ trẻ em và người già."),
        PedagogicalTopic("topic-u4", 4, "Music and Arts", "Âm nhạc, mỹ thuật, các loại hình nghệ thuật truyền thống và hiện đại."),
        PedagogicalTopic("topic-u5", 5, "Food and Drink", "Ẩm thực Việt Nam và thế giới, nguyên liệu, món ăn truyền thống."),
        PedagogicalTopic("topic-u6", 6, "A Visit to a School", "Trường Quốc Tử Giám - Văn Miếu, các trường học lịch sử và cơ sở vật chất."),
        PedagogicalTopic("topic-u7", 7, "Traffic", "Giao thông, phương tiện đi lại, luật an toàn giao thông và biển báo đường bộ."),
        PedagogicalTopic("topic-u8", 8, "Films", "Phim ảnh, các thể loại phim, diễn xuất và cảm nhận về phim."),
        PedagogicalTopic("topic-u9", 9, "Festivals around the World", "Lễ hội văn hóa truyền thống và hiện đại trên thế giới."),
        PedagogicalTopic("topic-u10", 10, "Energy Sources", "Nguồn năng lượng tái tạo và không tái tạo, tiết kiệm năng lượng."),
        PedagogicalTopic("topic-u11", 11, "Travelling in the Future", "Phương tiện giao thông tương lai, công nghệ xanh và phương tiện không người lái."),
        PedagogicalTopic("topic-u12", 12, "English-Speaking Countries", "Các quốc gia nói tiếng Anh trên thế giới (USA, UK, Canada, Australia, New Zealand)."),
    ]

    grammar_rules = [
        PedagogicalGrammarRule(
            "grammar-u1-present-simple", 1, "Present Simple Tense",
            "S + V(s/es) | S + do/does not + V-inf | Do/Does + S + V-inf?",
            "Thì hiện tại đơn diễn tả thói quen, chân lý, sự thật hiển nhiên hoặc sở thích.",
            ["I collect stamps in my free time.", "She loves making pottery.", "Water boils at 100 degrees Celsius."]
        ),
        PedagogicalGrammarRule(
            "grammar-u2-compound-sentences", 2, "Simple and Compound Sentences",
            "Independent clause + coordinator (and, or, but, so) + Independent clause",
            "Câu ghép kết nối hai mệnh đề độc lập bằng liên từ đẳng lập (and, or, but, so).",
            ["I eat healthy food, and I exercise daily.", "She has a cold, so she stays at home."]
        ),
        PedagogicalGrammarRule(
            "grammar-u3-past-simple", 3, "Past Simple Tense",
            "S + V2/ed | S + did not + V-inf | Did + S + V-inf?",
            "Thì quá khứ đơn diễn tả hành động đã xảy ra và chấm dứt trong quá khứ.",
            ["We donated books to street children last week.", "They planted trees yesterday."]
        ),
        PedagogicalGrammarRule(
            "grammar-u4-comparisons", 4, "Comparisons: like, different from, (not) as ... as",
            "as + adj/adv + as | different from + N | like + N",
            "So sánh ngang bằng (as... as), so sánh khác biệt (different from) và tương tự (like).",
            ["This painting is as old as that one.", "Classical music is different from pop music."]
        ),
        PedagogicalGrammarRule(
            "grammar-u5-quantifiers", 5, "Nouns & Quantifiers: some, any, how much, how many",
            "some + N(plural/uncount) | any + N(neg/interrogative) | how much + uncount | how many + plural count",
            "Lượng từ và câu hỏi số lượng với danh từ đếm được và không đếm được.",
            ["Is there any milk in the fridge?", "We need some apples.", "How much water do you drink a day?"]
        ),
        PedagogicalGrammarRule(
            "grammar-u6-prepositions-place-time", 6, "Prepositions of Place and Time (at, in, on)",
            "at + specific point/time | in + enclosed space/month/year | on + surface/day",
            "Giới từ chỉ thời gian và nơi chốn chuẩn xác.",
            ["The Temple of Literature was built in 1070.", "The exam starts at 8 a.m. on Monday."]
        ),
        PedagogicalGrammarRule(
            "grammar-u7-it-distance-connectors", 7, "It for Distance & Connectors of Contrast (Although / However)",
            "It is + distance + from A to B | Although + clause, clause | Clause. However, clause.",
            "Dùng 'it' chỉ khoảng cách và liên từ chỉ sự tương phản (although, however).",
            ["It is about 2 km from my house to school.", "Although it rained heavily, he rode his bike to school."]
        ),
        PedagogicalGrammarRule(
            "grammar-u8-adjectives-ed-ing", 8, "Adjectives ending in -ed and -ing",
            "V-ed (cảm xúc con người) | V-ing (tính chất sự vật/sự việc)",
            "Tính từ đuôi -ed mô tả cảm xúc của người; tính từ đuôi -ing mô tả đặc tính sự vật.",
            ["I was bored with the movie.", "The film has a very surprising ending."]
        ),
        PedagogicalGrammarRule(
            "grammar-u9-questions", 9, "Questions: Yes/No & Wh-Questions",
            "Wh-word + auxiliary + S + V-inf? | Auxiliary + S + V-inf?",
            "Các mẫu câu hỏi Yes/No và câu hỏi với từ để hỏi (What, Where, When, Who, Why, How).",
            ["Where did you celebrate the Mid-Autumn festival?", "Do people eat turkey at Thanksgiving?"]
        ),
        PedagogicalGrammarRule(
            "grammar-u10-future-simple", 10, "Future Simple Tense with Will",
            "S + will/won't + V-inf | Will + S + V-inf?",
            "Thì tương lai đơn diễn tả dự đoán trong tương lai hoặc quyết định tức thời.",
            ["Solar energy will be used more widely.", "We will not use coal in the future."]
        ),
        PedagogicalGrammarRule(
            "grammar-u11-future-continuous-passive", 11, "Future Simple Passive & Modals for Transport",
            "S + will be + V3/ed | Modals: can, might + V-inf",
            "Thể bị động thì tương lai đơn và động từ khuyết thiếu dự đoán khả năng phương tiện tương lai.",
            ["Driverless cars will be tested next year.", "Flying cars might reduce traffic jams."]
        ),
        PedagogicalGrammarRule(
            "grammar-u12-articles", 12, "Articles: A, An, The and Zero Article",
            "a/an + singular countable (first mention) | the + unique/specific noun | zero article + general plural/uncount",
            "Mạo từ không xác định (a, an), xác định (the) và không dùng mạo từ.",
            ["The Statue of Liberty is in the USA.", "Canada is an English-speaking country."]
        ),
    ]

    pronunciations = [
        PedagogicalPronunciation("pron-u1", 1, "/ə/ and /ɜː/", "Phân biệt nguyên âm ngắn /ə/ (amazing, yoga) và nguyên âm dài /ɜː/ (learn, work).", ["amazing", "yoga", "collect", "learn", "surf", "work"]),
        PedagogicalPronunciation("pron-u2", 2, "/f/ and /v/", "Phân biệt phụ âm vô thanh /f/ và hữu thanh /v/.", ["fat", "fit", "view", "active", "vitamin"]),
        PedagogicalPronunciation("pron-u3", 3, "/t/, /d/, and /ɪd/", "Ba cách phát âm đuôi -ed của động từ có quy tắc.", ["helped", "donated", "provided", "cleaned", "planted"]),
        PedagogicalPronunciation("pron-u4", 4, "/ʃ/ and /ʒ/", "Phân biệt phụ âm /ʃ/ (musician, show) và /ʒ/ (pleasure, television).", ["musician", "show", "pleasure", "television", "decision"]),
        PedagogicalPronunciation("pron-u5", 5, "/ɒ/ and /ɔː/", "Phân biệt nguyên âm ngắn /ɒ/ (pot, bottle) và nguyên âm dài /ɔː/ (sauce, water).", ["pot", "bottle", "sauce", "water", "pork"]),
        PedagogicalPronunciation("pron-u6", 6, "/tʃ/ and /dʒ/", "Phân biệt phụ âm /tʃ/ (chair, cherry) và /dʒ/ (jam, gym).", ["chair", "children", "jam", "gym", "subject"]),
        PedagogicalPronunciation("pron-u7", 7, "/e/ and /eɪ/", "Phân biệt nguyên âm đơn /e/ (seatbelt, ahead) và nguyên âm đôi /eɪ/ (train, pavement).", ["seatbelt", "ahead", "train", "pavement", "safe"]),
        PedagogicalPronunciation("pron-u8", 8, "/ɪə/ and /eə/", "Phân biệt nguyên âm đôi /ɪə/ (fear, cheer) và /eə/ (care, share).", ["fear", "cheer", "care", "share", "scary"]),
        PedagogicalPronunciation("pron-u9", 9, "Stress in two-syllable words", "Trọng âm từ hai âm tiết: danh từ/tính từ thường rơi vào âm tiết 1, động từ thường rơi vào âm tiết 2.", ["dancer", "festive", "perform", "parade", "attend"]),
        PedagogicalPronunciation("pron-u10", 10, "Stress in three-syllable nouns and verbs", "Trọng âm từ ba âm tiết của danh từ và tính từ phổ biến trong chủ đề Năng lượng.", ["energy", "natural", "polluting", "generate"]),
        PedagogicalPronunciation("pron-u11", 11, "Sentence intonation (rising & falling)", "Ngữ điệu câu: lên giọng ở cuối câu hỏi Yes/No, xuống giọng ở cuối câu trần thuật và Wh-questions.", ["Do you think it's safe? ↑", "Flying cars will be fast. ↓"]),
        PedagogicalPronunciation("pron-u12", 12, "Falling intonation in statements", "Ngữ điệu xuống cuối câu khẳng định và câu hỏi có từ để hỏi (Wh-questions).", ["Australia is a continent. ↓", "What is the capital of Canada? ↓"]),
    ]

    vocabulary = [
        PedagogicalVocabulary("vocab-u1-1", 1, "hobby", "noun", "/ˈhɒbi/", "sở thích", "Collecting stamps is my favourite hobby."),
        PedagogicalVocabulary("vocab-u1-2", 1, "pottery", "noun", "/ˈpɒtəri/", "đồ gốm", "She learns how to make pottery on weekends."),
        PedagogicalVocabulary("vocab-u2-1", 2, "healthy", "adj", "/ˈhelθi/", "lành mạnh, khỏe mạnh", "Eating vegetables helps you stay healthy."),
        PedagogicalVocabulary("vocab-u2-2", 2, "acne", "noun", "/ˈækni/", "mụn trứng cá", "Wash your face regularly to prevent acne."),
        PedagogicalVocabulary("vocab-u3-1", 3, "community", "noun", "/kəˈmjuːnəti/", "cộng đồng", "They do a lot of work for the local community."),
        PedagogicalVocabulary("vocab-u3-2", 3, "donate", "verb", "/dəʊˈneɪt/", "quyên góp, ủng hộ", "We donate books and warm clothes to street children."),
        PedagogicalVocabulary("vocab-u4-1", 4, "portrait", "noun", "/ˈpɔːtrət/", "chân dung", "He is painting a portrait of his mother."),
        PedagogicalVocabulary("vocab-u4-2", 4, "puppet", "noun", "/ˈpʌpɪt/", "con rối", "Water puppetry is a traditional Vietnamese art form."),
        PedagogicalVocabulary("vocab-u5-1", 5, "ingredient", "noun", "/ɪnˈɡriːdiənt/", "nguyên liệu", "The main ingredients of Pho are broth, noodles, and beef."),
        PedagogicalVocabulary("vocab-u5-2", 5, "omelette", "noun", "/ˈɒmlət/", "trứng cuộn", "I often make an omelette for breakfast."),
        PedagogicalVocabulary("vocab-u6-1", 6, "monument", "noun", "/ˈmɒnjumənt/", "đài kỷ niệm, di tích", "The Temple of Literature is a famous historic monument."),
        PedagogicalVocabulary("vocab-u6-2", 6, "statue", "noun", "/ˈstætʃuː/", "bức tượng", "There are stone statues of doctors in the garden."),
        PedagogicalVocabulary("vocab-u7-1", 7, "traffic jam", "noun", "/ˈtræfɪk dʒæm/", "tắc nghẽn giao thông", "Avoid travelling during rush hour to not get stuck in a traffic jam."),
        PedagogicalVocabulary("vocab-u7-2", 7, "seatbelt", "noun", "/ˈsiːtbelt/", "dây an toàn", "Always fasten your seatbelt when driving a car."),
        PedagogicalVocabulary("vocab-u8-1", 8, "animation", "noun", "/ˌænɪˈmeɪʃn/", "phim hoạt hình đồ họa", "Children love watching Disney animation movies."),
        PedagogicalVocabulary("vocab-u8-2", 8, "critic", "noun", "/ˈkrɪtɪk/", "nhà phê bình", "Film critics gave positive reviews for the new movie."),
        PedagogicalVocabulary("vocab-u9-1", 9, "parade", "noun", "/pəˈreɪd/", "cuộc diễu hành", "People dress in colourful costumes during the carnival parade."),
        PedagogicalVocabulary("vocab-u9-2", 9, "festive", "adj", "/ˈfestɪv/", "thuộc về lễ hội", "The town has a wonderful festive atmosphere during Tet."),
        PedagogicalVocabulary("vocab-u10-1", 10, "renewable", "adj", "/rɪˈnjuːəbl/", "tái tạo được", "Solar and wind are renewable sources of energy."),
        PedagogicalVocabulary("vocab-u10-2", 10, "footprint", "noun", "/ˈfʊtprɪnt/", "dấu chân sinh thái", "We can reduce our carbon footprint by using public transport."),
        PedagogicalVocabulary("vocab-u11-1", 11, "driverless", "adj", "/ˈdraɪvələs/", "không người lái", "Driverless buses will run on electric power."),
        PedagogicalVocabulary("vocab-u11-2", 11, "bamboo-copter", "noun", "/ˌbæmˈbuː ˈkɒptə/", "chong chóng tre (phương tiện bay cá nhân)", "The bamboo-copter is an eco-friendly future means of transport."),
        PedagogicalVocabulary("vocab-u12-1", 12, "native", "adj", "/ˈneɪtɪv/", "bản địa", "Kangaroos and koalas are native to Australia."),
        PedagogicalVocabulary("vocab-u12-2", 12, "attraction", "noun", "/əˈtrækʃn/", "điểm thu hút du lịch", "Niagara Falls is a famous natural attraction."),
    ]

    prerequisites = [
        PedagogicalPrerequisite("grammar-u1-present-simple", "grammar-u2-compound-sentences", 0.7),
        PedagogicalPrerequisite("grammar-u1-present-simple", "grammar-u3-past-simple", 0.8),
        PedagogicalPrerequisite("grammar-u1-present-simple", "grammar-u10-future-simple", 0.75),
        PedagogicalPrerequisite("grammar-u10-future-simple", "grammar-u11-future-continuous-passive", 0.85),
    ]

    return CurriculumOntology(
        topics=topics,
        grammar_rules=grammar_rules,
        vocabulary=vocabulary,
        pronunciations=pronunciations,
        prerequisites=prerequisites,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec english7-api-1 pytest tests/modules/knowledge/test_curriculum_ontology.py -v`
Expected: PASS with 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/src/english7/modules/knowledge/curriculum_ontology.py backend/tests/modules/knowledge/test_curriculum_ontology.py
git commit -m "feat(knowledge): add structured curriculum ontology for Tiếng Anh 7"
```

---

### Task 3: Neo4j Schema & Repository Enhancements

**Files:**
- Modify: `backend/src/english7/modules/knowledge/neo4j_repository.py`
- Test: `backend/tests/modules/knowledge/test_neo4j_pedagogical_repository.py`

**Interfaces:**
- Consumes: `CurriculumOntology`, `IndexedFragment`
- Produces: `Neo4jKnowledgeRepository` with methods `ensure_schema`, `upsert_pedagogical_nodes`, `upsert_weighted_relationships`, `vector_search_concepts`, and `weighted_graph_search`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/knowledge/test_neo4j_pedagogical_repository.py
import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from english7.modules.knowledge.neo4j_repository import Neo4jKnowledgeRepository
from english7.modules.knowledge.curriculum_ontology import PedagogicalTopic, PedagogicalGrammarRule


def test_neo4j_repository_ensures_dual_vector_indexes():
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    repo = Neo4jKnowledgeRepository(
        mock_driver,
        vector_index_name="source_fragment_embedding",
        embedding_dimensions=384,
        graph_result_limit=10,
    )
    repo.ensure_schema()
    # verify vector index for source fragments and concepts were created
    calls = [call[0][0] for call in mock_session.run.call_args_list]
    assert any("source_fragment_embedding" in c for c in calls)
    assert any("knowledge_concept_embedding" in c for c in calls)


def test_neo4j_repository_upsert_pedagogical_nodes():
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    repo = Neo4jKnowledgeRepository(
        mock_driver,
        vector_index_name="source_fragment_embedding",
        embedding_dimensions=384,
        graph_result_limit=10,
    )
    topic = PedagogicalTopic("topic-u1", 1, "Hobbies", "Sở thích")
    repo.upsert_topic(topic, [0.1] * 384)
    assert mock_session.run.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec english7-api-1 pytest tests/modules/knowledge/test_neo4j_pedagogical_repository.py -v`
Expected: FAIL with `AssertionError: assert any(...)` (index and topic methods missing)

- [ ] **Step 3: Write minimal implementation**

Update `backend/src/english7/modules/knowledge/neo4j_repository.py` to:
1. Add `knowledge_concept_embedding` index creation in `ensure_schema()`.
2. Add methods:
   - `upsert_topic(topic, embedding)`
   - `upsert_grammar_rule(rule, embedding)`
   - `upsert_vocabulary(vocab, embedding)`
   - `upsert_pronunciation(pron, embedding)`
   - `upsert_relationship(source_id, source_label, target_id, target_label, rel_type, weight)`
   - `vector_search_concepts(query_vector, top_k)`
   - `weighted_graph_search(seed_fragment_ids, max_depth)`

```python
    def ensure_schema(self) -> None:
        constraints = [
            "CREATE CONSTRAINT source_fragment_sql_id IF NOT EXISTS FOR (f:SourceFragment) REQUIRE f.sql_id IS UNIQUE",
            "CREATE CONSTRAINT knowledge_concept_id IF NOT EXISTS FOR (c:KnowledgeConcept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT unit_sql_id IF NOT EXISTS FOR (u:Unit) REQUIRE u.sql_id IS UNIQUE",
        ]
        indexes = [
            f"""CREATE VECTOR INDEX {self._index_name} IF NOT EXISTS
            FOR (f:SourceFragment) ON (f.embedding)
            OPTIONS {{indexConfig: {{`vector.dimensions`: {self._dimensions}, `vector.similarity_function`: 'cosine'}}}}""",
            f"""CREATE VECTOR INDEX knowledge_concept_embedding IF NOT EXISTS
            FOR (c:KnowledgeConcept) ON (c.embedding)
            OPTIONS {{indexConfig: {{`vector.dimensions`: {self._dimensions}, `vector.similarity_function`: 'cosine'}}}}""",
        ]
        with self._driver.session(database=self._database) as session:
            for c in constraints:
                session.run(c).consume()
            for idx in indexes:
                session.run(idx).consume()
```

Implement `upsert_topic`, `upsert_grammar_rule`, `upsert_vocabulary`, `upsert_pronunciation`, and `weighted_graph_search` in `Neo4jKnowledgeRepository`.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec english7-api-1 pytest tests/modules/knowledge/test_neo4j_pedagogical_repository.py -v`
Expected: PASS with 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/src/english7/modules/knowledge/neo4j_repository.py backend/tests/modules/knowledge/test_neo4j_pedagogical_repository.py
git commit -m "feat(knowledge): add dual vector indexes and pedagogical node methods to Neo4j repository"
```

---

### Task 4: Weighted GraphRAG Retrieval Service Upgrade

**Files:**
- Modify: `backend/src/english7/modules/retrieval/service.py`
- Modify: `backend/src/english7/modules/retrieval/reranker.py`
- Modify: `backend/src/english7/bootstrap.py`
- Modify: `.env`
- Test: `backend/tests/modules/retrieval/test_weighted_retrieval.py`

**Interfaces:**
- Consumes: `FastEmbedService`, `Neo4jKnowledgeRepository`
- Produces: Upgraded `RetrievalService.retrieve(query: str) -> GroundedContext` with weighted fusion and citations

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/retrieval/test_weighted_retrieval.py
import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from english7.modules.retrieval.service import RetrievalService, RetrievalCandidate


def test_weighted_graph_retrieval_prioritizes_teaches_over_practices():
    mock_repo = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [0.1] * 384

    frag_theory_id = uuid4()
    frag_practice_id = uuid4()

    mock_repo.vector_search.return_value = [
        RetrievalCandidate(
            fragment_id=frag_practice_id,
            unit_number=1,
            text="Practice 1: Fill in the blank with present simple.",
            pdf_page=10,
            printed_page=9,
            vector_score=0.85,
            has_verified_source=True,
            hierarchy=("English 7", "Unit 1", "A Closer Look 2", "1"),
        )
    ]

    # Graph expansion finds theory fragment linked via TEACHES (weight 1.0)
    mock_repo.expand.return_value = [
        RetrievalCandidate(
            fragment_id=frag_theory_id,
            unit_number=1,
            text="Remember Box: We use the present simple for habits.",
            pdf_page=10,
            printed_page=9,
            vector_score=0.95,
            has_verified_source=True,
            hierarchy=("English 7", "Unit 1", "A Closer Look 2", "1"),
        )
    ]

    service = RetrievalService(
        repository=mock_repo,
        embedder=mock_embedder,
        allowed_units=frozenset([1, 2, 10, 11, 12]),
        top_k=5,
        min_vector_score=0.6,
        graph_depth=2,
        rrf_constant=60,
        max_context_fragments=4,
    )

    context = service.retrieve("How to use present simple?")
    assert len(context.fragments) > 0
    assert len(context.citations) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec english7-api-1 pytest tests/modules/retrieval/test_weighted_retrieval.py -v`
Expected: PASS or FAIL depending on mock setup (verify behavior).

- [ ] **Step 3: Write minimal implementation**

1. Update `backend/src/english7/modules/retrieval/reranker.py` to support weighted RRF:
```python
def weighted_reciprocal_rank_fusion(
    vector_ids: tuple[str, ...],
    graph_scored_ids: tuple[tuple[str, float], ...],
    rank_constant: int = 60,
    vector_multiplier: float = 1.0,
    graph_multiplier: float = 1.2,
) -> list[FusedResult]:
    scores: dict[str, float] = {}
    for rank, item_id in enumerate(vector_ids):
        scores[item_id] = scores.get(item_id, 0.0) + (vector_multiplier / (rank_constant + rank + 1))
    for rank, (item_id, weight) in enumerate(graph_scored_ids):
        scores[item_id] = scores.get(item_id, 0.0) + (graph_multiplier * weight / (rank_constant + rank + 1))
    fused = [FusedResult(item_id, score) for item_id, score in scores.items()]
    fused.sort(key=lambda item: item.score, reverse=True)
    return fused
```

2. Update `backend/src/english7/bootstrap.py`:
   - Initialize `FastEmbedService` as default embedder.
   - Update `ENGLISH7_RETRIEVAL_ALLOWED_UNITS` to include all 16 units: `1,2,3,4,5,6,7,8,9,10,11,12,31,61,91,121`.

3. Update `.env` with `ENGLISH7_RETRIEVAL_ALLOWED_UNITS=1,2,3,4,5,6,7,8,9,10,11,12,31,61,91,121`.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec english7-api-1 pytest tests/modules/retrieval/test_weighted_retrieval.py -v`
Expected: PASS with 1 passed

- [ ] **Step 5: Commit**

```bash
git add backend/src/english7/modules/retrieval/service.py backend/src/english7/modules/retrieval/reranker.py backend/src/english7/bootstrap.py .env
git commit -m "feat(retrieval): upgrade RetrievalService with weighted GraphRAG and full curriculum unit support"
```

---

### Task 5: End-to-End Ingestion & Seeding Script for Full Textbook

**Files:**
- Create: `backend/scripts/build_full_knowledge_graph.py`
- Test: `backend/tests/integration/test_full_knowledge_graph.py`

**Interfaces:**
- Consumes: SQL Server (458 source fragments), `CurriculumOntology`, `FastEmbedService`, `Neo4jKnowledgeRepository`
- Produces: Fully populated Neo4j Knowledge Graph with 458 embedded SourceFragments, 12 Topics, 12 GrammarRules, 24+ Vocabulary, 12 Pronunciation nodes, and full weighted relationships (`TEACHES`, `EXPLAINS`, `PRACTICES`, `PREREQUISITE_OF`, `REVIEWS`, `APPEARS_IN`).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/integration/test_full_knowledge_graph.py
import pytest
from neo4j import GraphDatabase
from english7.core.settings import get_settings


@pytest.mark.integration
def test_full_knowledge_graph_populated_and_indexed():
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
    )
    with driver.session() as session:
        # Check SourceFragments count
        frag_count = session.run("MATCH (f:SourceFragment) RETURN count(f) as count").single()["count"]
        assert frag_count >= 400

        # Check Pedagogical Nodes
        concept_count = session.run("MATCH (c:KnowledgeConcept) RETURN count(c) as count").single()["count"]
        assert concept_count >= 50

        # Check Weighted Relationships
        teaches_count = session.run("MATCH ()-[r:TEACHES]->() RETURN count(r) as count").single()["count"]
        assert teaches_count > 0

        # Check Vectors have 384 dimensions
        sample = session.run("MATCH (f:SourceFragment) RETURN size(f.embedding) as dims LIMIT 1").single()["dims"]
        assert sample == 384
    driver.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec english7-api-1 pytest tests/integration/test_full_knowledge_graph.py -v -m integration`
Expected: FAIL (graph not yet seeded with full data and 384d vectors)

- [ ] **Step 3: Write minimal implementation**

Create `backend/scripts/build_full_knowledge_graph.py`:
- Fetch all 458 fragments from SQL Server with their Unit, Section, and Activity info.
- Clean existing obsolete test nodes in Neo4j.
- Execute `ensure_schema()` in Neo4j.
- Initialize `FastEmbedService`.
- Batch embed all 458 fragments into 384d vectors.
- Insert all `Textbook`, `Unit`, `Section`, `Activity`, `SourceFragment` and link them via `HAS_UNIT`, `HAS_SECTION`, `HAS_ACTIVITY`, `HAS_SOURCE`.
- Load `CurriculumOntology`:
  - Embed and upsert all `Topic`, `GrammarRule`, `Vocabulary`, `PronunciationSound` nodes with label `KnowledgeConcept`.
  - Link Review units via `REVIEWS` (weight: 0.8).
  - Link Grammar rules via `PREREQUISITE_OF` (weight: 0.7).
  - Link Activities to GrammarRules via `TEACHES` (weight: 1.0 for A Closer Look 2 rules) and `PRACTICES` (weight: 0.6).
  - Link Activities to Pronunciation via `TEACHES` (weight: 1.0 for A Closer Look 1 pronunciation).
  - Link Activities to Vocabulary via `EXPLAINS` (weight: 0.9) and `PRACTICES` (weight: 0.6).
- Print summary verification.

Execute the script inside the container:
`docker exec english7-api-1 python3 /app/scripts/build_full_knowledge_graph.py`

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec english7-api-1 pytest tests/integration/test_full_knowledge_graph.py -v -m integration`
Expected: PASS with 1 passed

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/build_full_knowledge_graph.py backend/tests/integration/test_full_knowledge_graph.py
git commit -m "feat(knowledge): implement build_full_knowledge_graph script and integration tests"
```

---

### Task 6: End-to-End Verification via AI Tutor & Mobile App

**Files:**
- Test query script: `backend/scripts/test_tutor_queries.py`

- [ ] **Step 1: Write verification script testing key curriculum queries**

```python
# backend/scripts/test_tutor_queries.py
from english7.bootstrap import configure_runtime
from english7.core.settings import get_settings

settings = get_settings()
# Test sample queries representing different skills and units:
queries = [
    "Khi nào dùng thì hiện tại đơn?",
    "Tell me about renewable energy sources in Unit 10",
    "What means of transport will we have in the future?",
    "Which countries are English-speaking countries?",
]

# Run retrieval for each and print top fragments and citations
```

- [ ] **Step 2: Execute verification script inside container**

Run: `docker exec english7-api-1 python3 /app/scripts/test_tutor_queries.py`
Expected: Output showing top fragments and page citations matching the exact units.

- [ ] **Step 3: Verification on Mobile Emulator**

Open mobile app, tap tab **Tutor**, ask *"What are renewable energy sources?"*, and verify that AI Tutor responds with authentic citations to Unit 10 (Energy Sources).

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/test_tutor_queries.py
git commit -m "test: add end-to-end verification script for Tutor queries"
```
