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
