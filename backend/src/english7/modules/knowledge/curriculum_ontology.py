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
        PedagogicalVocabulary("vocab-u1-2", 1, "dollhouse", "noun", "/ˈdɒlhaʊs/", "nhà búp bê", "I like building dollhouses."),
        PedagogicalVocabulary("vocab-u1-3", 1, "gardening", "noun", "/ˈɡɑːdnɪŋ/", "việc làm vườn", "My father loves gardening."),
        PedagogicalVocabulary("vocab-u1-4", 1, "collect", "verb", "/kəˈlekt/", "sưu tầm", "I collect coins from different countries."),
        PedagogicalVocabulary("vocab-u1-5", 1, "coins", "noun", "/kɔɪnz/", "những đồng xu", "I have a lot of coins from different countries."),
        PedagogicalVocabulary("vocab-u1-6", 1, "stamps", "noun", "/stæmps/", "những con tem", "My brother collects foreign stamps."),
        PedagogicalVocabulary("vocab-u1-7", 1, "model", "noun", "/ˈmɒdl/", "mô hình", "They like making models in their free time."),
        PedagogicalVocabulary("vocab-u1-8", 1, "jogging", "noun", "/ˈdʒɒɡɪŋ/", "chạy bộ", "Jogging helps you stay fit."),
        PedagogicalVocabulary("vocab-u1-9", 1, "yoga", "noun", "/ˈjəʊɡə/", "môn yoga", "My sister does yoga every morning."),
        PedagogicalVocabulary("vocab-u1-10", 1, "judo", "noun", "/ˈdʒuːdəʊ/", "môn võ judo", "He goes to the judo club twice a week."),
        PedagogicalVocabulary("vocab-u1-11", 1, "swimming", "noun", "/ˈswɪmɪŋ/", "bơi lội", "Swimming is good for your health."),
        PedagogicalVocabulary("vocab-u1-12", 1, "patient", "adj", "/ˈpeɪʃnt/", "kiên nhẫn", "You need to be patient when making pottery."),
        PedagogicalVocabulary("vocab-u1-13", 1, "patience", "noun", "/ˈpeɪʃns/", "lòng kiên nhẫn", "Gardening teaches children patience and responsibility."),
        PedagogicalVocabulary("vocab-u1-14", 1, "responsibility", "noun", "/rɪˌspɒnsəˈbɪləti/", "tinh thần trách nhiệm", "Taking care of plants teaches responsibility."),
        PedagogicalVocabulary("vocab-u1-15", 1, "benefit", "noun", "/ˈbenɪfɪt/", "lợi ích", "What are the benefits of your hobby?"),
        PedagogicalVocabulary("vocab-u1-16", 1, "relax", "verb", "/rɪˈlæks/", "thư giãn", "Gardening helps you relax and reduce stress."),
        PedagogicalVocabulary("vocab-u1-17", 1, "creative", "adj", "/kriˈeɪtɪv/", "sáng tạo", "Making handicrafts helps you become more creative."),
        PedagogicalVocabulary("vocab-u1-18", 1, "bookshelf", "noun", "/ˈbʊkʃelf/", "giá sách", "My dad has a big bookshelf in his room."),
        PedagogicalVocabulary("vocab-u1-19", 1, "insect", "noun", "/ˈɪnsekt/", "côn trùng", "Gardening teaches children about flowers and insects."),
        PedagogicalVocabulary("vocab-u1-20", 1, "climbing", "noun", "/ˈklaɪmɪŋ/", "leo trèo, leo núi", "Mountain climbing is a challenging hobby."),
        PedagogicalVocabulary("vocab-u1-21", 1, "unusual", "adj", "/ʌnˈjuːʒuəl/", "khác thường, độc đáo", "My sister has an unusual hobby."),
        PedagogicalVocabulary("vocab-u1-22", 1, "maturity", "noun", "/məˈtʃʊərəti/", "sự trưởng thành", "Hobbies help children develop maturity."),
        PedagogicalVocabulary("vocab-u1-23", 1, "dolls", "noun", "/dɒlz/", "những con búp bê", "My hobby is collecting dolls."),
        PedagogicalVocabulary("vocab-u1-24", 1, "ice skating", "noun", "/ˈaɪs skeɪtɪŋ/", "trượt băng", "My brother doesn't like ice skating."),
        PedagogicalVocabulary("vocab-u1-25", 1, "horse riding", "noun", "/ˈhɔːs raɪdɪŋ/", "cưỡi ngựa", "Riding a horse is very exciting."),
        PedagogicalVocabulary("vocab-u2-1", 2, "healthy", "adj", "/ˈhelθi/", "lành mạnh, khỏe mạnh", "Eating vegetables helps you stay healthy."),
        PedagogicalVocabulary("vocab-u2-2", 2, "health", "noun", "/helθ/", "sức khỏe", "Good food is important for your health."),
        PedagogicalVocabulary("vocab-u2-3", 2, "acne", "noun", "/ˈækni/", "mụn trứng cá", "Wash your face regularly to prevent acne."),
        PedagogicalVocabulary("vocab-u2-4", 2, "dim light", "noun", "/dɪm laɪt/", "ánh sáng yếu", "Reading in dim light harms your eyes."),
        PedagogicalVocabulary("vocab-u2-5", 2, "sunburn", "noun", "/ˈsʌnbɜːn/", "sự cháy nắng", "Wear a hat and suncream to avoid sunburn."),
        PedagogicalVocabulary("vocab-u2-6", 2, "suncream", "noun", "/ˈsʌnkriːm/", "kem chống nắng", "Apply suncream when going outdoors."),
        PedagogicalVocabulary("vocab-u2-7", 2, "chapped lips", "noun", "/tʃæpt lɪps/", "môi nứt nẻ", "Drinking enough water prevents chapped lips."),
        PedagogicalVocabulary("vocab-u2-8", 2, "skin", "noun", "/skɪn/", "làn da", "Vegetables and water keep your skin smooth."),
        PedagogicalVocabulary("vocab-u2-9", 2, "vegetables", "noun", "/ˈvedʒtəblz/", "rau củ", "Eat lots of fresh coloured vegetables."),
        PedagogicalVocabulary("vocab-u2-10", 2, "fruit", "noun", "/fruːt/", "trái cây, hoa quả", "Fresh fruit provides important vitamins."),
        PedagogicalVocabulary("vocab-u2-11", 2, "active", "adj", "/ˈæktɪv/", "năng động, tích cực", "Outdoor activities keep you active and strong."),
        PedagogicalVocabulary("vocab-u2-12", 2, "tired", "adj", "/ˈtaɪəd/", "mệt mỏi", "I feel tired after working for hours."),
        PedagogicalVocabulary("vocab-u2-13", 2, "fit", "adj", "/fɪt/", "cân đối, khỏe mạnh", "Exercise daily to keep fit and healthy."),
        PedagogicalVocabulary("vocab-u2-14", 2, "keep fit", "verb", "/kiːp fɪt/", "giữ dáng, giữ sức khỏe", "Playing sports helps us keep fit."),
        PedagogicalVocabulary("vocab-u2-15", 2, "energy", "noun", "/ˈenədʒi/", "năng lượng", "Healthy food gives you energy for the whole day."),
        PedagogicalVocabulary("vocab-u2-16", 2, "weight", "noun", "/weɪt/", "cân nặng", "Fast food can make you gain weight."),
        PedagogicalVocabulary("vocab-u2-17", 2, "avoid", "verb", "/əˈvɔɪd/", "tránh, né tránh", "Avoid drinking too much soda and sweetened drinks."),
        PedagogicalVocabulary("vocab-u2-18", 2, "soft drink", "noun", "/sɒft drɪŋk/", "nước ngọt có ga", "Soft drinks contain lots of sugar."),
        PedagogicalVocabulary("vocab-u2-19", 2, "fast food", "noun", "/fɑːst fuːd/", "thức ăn nhanh", "Eating too much fast food is harmful."),
        PedagogicalVocabulary("vocab-u2-20", 2, "outdoor", "adj", "/ˈaʊtdɔː/", "ngoài trời", "We should take part in outdoor activities."),
        PedagogicalVocabulary("vocab-u2-21", 2, "cycling", "noun", "/ˈsaɪklɪŋ/", "đi xe đạp", "Cycling to school is a great form of exercise."),
        PedagogicalVocabulary("vocab-u2-22", 2, "exercise", "noun", "/ˈeksəsaɪz/", "bài tập thể dục", "Morning exercise makes you feel energetic."),
        PedagogicalVocabulary("vocab-u2-23", 2, "clean", "adj", "/kliːn/", "sạch sẽ", "Keep your hands and face clean."),
        PedagogicalVocabulary("vocab-u2-24", 2, "lifestyle", "noun", "/ˈlaɪfstaɪl/", "lối sống", "A healthy lifestyle leads to a happy life."),
        PedagogicalVocabulary("vocab-u2-25", 2, "tofu", "noun", "/ˈtəʊfuː/", "đậu phụ", "Tofu is a healthy, low-fat source of protein."),
        PedagogicalVocabulary("vocab-u3-1", 3, "community", "noun", "/kəˈmjuːnəti/", "cộng đồng", "They do a lot of work for the local community."),
        PedagogicalVocabulary("vocab-u3-2", 3, "community service", "noun", "/kəˈmjuːnəti ˈsɜːvɪs/", "phục vụ cộng đồng", "Community service helps disadvantaged people."),
        PedagogicalVocabulary("vocab-u3-3", 3, "volunteer", "noun", "/ˌvɒlənˈtɪə/", "tình nguyện viên", "She works as a volunteer at the hospital."),
        PedagogicalVocabulary("vocab-u3-4", 3, "donate", "verb", "/dəʊˈneɪt/", "quyên góp, ủng hộ", "We donate books and warm clothes to street children."),
        PedagogicalVocabulary("vocab-u3-5", 3, "donation", "noun", "/dəʊˈneɪʃn/", "sự quyên góp", "Thank you very much for your donation."),
        PedagogicalVocabulary("vocab-u3-6", 3, "elderly", "adj", "/ˈeldəli/", "người cao tuổi", "Students visit and help elderly people in nursing homes."),
        PedagogicalVocabulary("vocab-u3-7", 3, "nursing home", "noun", "/ˈnɜːsɪŋ həʊm/", "viện dưỡng lão", "They sing songs for the elderly at the nursing home."),
        PedagogicalVocabulary("vocab-u3-8", 3, "street children", "noun", "/striːt ˈtʃɪldrən/", "trẻ em đường phố", "We provide free meals for street children."),
        PedagogicalVocabulary("vocab-u3-9", 3, "orphanage", "noun", "/ˈɔːfənɪdʒ/", "trại trẻ mồ côi", "Our club visited an orphanage last Sunday."),
        PedagogicalVocabulary("vocab-u3-10", 3, "homeless", "adj", "/ˈhəʊmləs/", "vô gia cư", "We cooked hot soup for homeless people."),
        PedagogicalVocabulary("vocab-u3-11", 3, "tutor", "verb", "/ˈtjuːtə/", "dạy kèm, phụ đạo", "Older students tutor younger kids in maths and English."),
        PedagogicalVocabulary("vocab-u3-12", 3, "clean up", "verb", "/kliːn ʌp/", "dọn dẹp vệ sinh", "Let's clean up the school playground together."),
        PedagogicalVocabulary("vocab-u3-13", 3, "litter", "noun", "/ˈlɪtə/", "rác rưởi", "Do not drop litter on the ground."),
        PedagogicalVocabulary("vocab-u3-14", 3, "rubbish", "noun", "/ˈrʌbɪʃ/", "rác thải", "Put rubbish into the waste bins."),
        PedagogicalVocabulary("vocab-u3-15", 3, "recycle", "verb", "/ˌriːˈsaɪkl/", "tái chế", "We recycle used paper and plastic bottles."),
        PedagogicalVocabulary("vocab-u3-16", 3, "plant trees", "verb", "/plɑːnt triːz/", "trồng cây xanh", "Volunteers plant trees along the neighborhood streets."),
        PedagogicalVocabulary("vocab-u3-17", 3, "exchange", "verb", "/ɪksˈtʃeɪndʒ/", "trao đổi", "Students exchange used books for paper flowers."),
        PedagogicalVocabulary("vocab-u3-18", 3, "provide", "verb", "/prəˈvaɪd/", "cung cấp", "The program provides free meals and notebooks."),
        PedagogicalVocabulary("vocab-u3-19", 3, "encourage", "verb", "/ɪnˈkʌrɪdʒ/", "khuyến khích, động viên", "Teachers encourage students to help poor children."),
        PedagogicalVocabulary("vocab-u3-20", 3, "project", "noun", "/ˈprɒdʒekt/", "dự án", "Our green school project was very successful."),
        PedagogicalVocabulary("vocab-u3-21", 3, "clothes", "noun", "/kləʊðz/", "quần áo", "We collect warm clothes for children in mountainous areas."),
        PedagogicalVocabulary("vocab-u3-22", 3, "pick up", "verb", "/pɪk ʌp/", "nhặt lên, thu gom", "We pick up plastic litter in the park."),
        PedagogicalVocabulary("vocab-u3-23", 3, "bottles", "noun", "/ˈbɒtlz/", "chai lọ", "Collect used plastic bottles for recycling."),
        PedagogicalVocabulary("vocab-u3-24", 3, "garden", "noun", "/ˈɡɑːdn/", "khu vườn", "Students take care of the community garden."),
        PedagogicalVocabulary("vocab-u3-25", 3, "help", "verb", "/help/", "giúp đỡ", "We are happy to help people in need."),
        PedagogicalVocabulary("vocab-u4-1", 4, "portrait", "noun", "/ˈpɔːtrət/", "chân dung", "He is painting a portrait of his mother."),
        PedagogicalVocabulary("vocab-u4-2", 4, "puppet", "noun", "/ˈpʌpɪt/", "con rối", "Water puppetry is a unique Vietnamese traditional art form."),
        PedagogicalVocabulary("vocab-u4-3", 4, "water puppet", "noun", "/ˈwɔːtə ˈpʌpɪt/", "con rối nước", "Water puppets dance on the surface of the pool."),
        PedagogicalVocabulary("vocab-u4-4", 4, "puppeteer", "noun", "/ˌpʌpɪˈtɪə/", "nghệ sĩ múa rối", "Puppeteers stand behind a bamboo screen in the water."),
        PedagogicalVocabulary("vocab-u4-5", 4, "composer", "noun", "/kəmˈpəʊzə/", "nhà soạn nhạc", "Van Cao was a famous Vietnamese composer."),
        PedagogicalVocabulary("vocab-u4-6", 4, "musical instrument", "noun", "/ˈmjuːzɪkl ˈɪnstrəmənt/", "nhạc cụ", "Can you play any musical instrument?"),
        PedagogicalVocabulary("vocab-u4-7", 4, "instrument", "noun", "/ˈɪnstrəmənt/", "nhạc cụ, dụng cụ", "The guitar is my favourite musical instrument."),
        PedagogicalVocabulary("vocab-u4-8", 4, "art gallery", "noun", "/ɑːt ˈɡæləri/", "phòng triển lãm tranh", "We saw many famous paintings at the art gallery."),
        PedagogicalVocabulary("vocab-u4-9", 4, "gallery", "noun", "/ˈɡæləri/", "phòng trưng bày", "The city gallery exhibits modern art."),
        PedagogicalVocabulary("vocab-u4-10", 4, "exhibition", "noun", "/ˌeksɪˈbɪʃn/", "cuộc triển lãm", "The photo exhibition attracts many visitors."),
        PedagogicalVocabulary("vocab-u4-11", 4, "anthem", "noun", "/ˈænθəm/", "bài quốc ca", "Tien Quan Ca is the national anthem of Viet Nam."),
        PedagogicalVocabulary("vocab-u4-12", 4, "musician", "noun", "/mjuːˈzɪʃn/", "nhạc sĩ", "She wants to become a talented musician."),
        PedagogicalVocabulary("vocab-u4-13", 4, "artist", "noun", "/ˈɑːtɪst/", "nghệ sĩ, họa sĩ", "The artist uses watercolours for this painting."),
        PedagogicalVocabulary("vocab-u4-14", 4, "actress", "noun", "/ˈæktrəs/", "nữ diễn viên", "She is a well-known television actress."),
        PedagogicalVocabulary("vocab-u4-15", 4, "concert", "noun", "/ˈkɒnsət/", "buổi hòa nhạc", "We attended an open-air concert last night."),
        PedagogicalVocabulary("vocab-u4-16", 4, "classical music", "noun", "/ˈklæsɪkl ˈmjuːzɪk/", "nhạc cổ điển", "Listening to classical music helps me focus."),
        PedagogicalVocabulary("vocab-u4-17", 4, "pop music", "noun", "/pɒp ˈmjuːzɪk/", "nhạc trẻ, nhạc pop", "Teenagers usually enjoy listening to pop music."),
        PedagogicalVocabulary("vocab-u4-18", 4, "folk music", "noun", "/fəʊk ˈmjuːzɪk/", "nhạc dân ca", "Folk music reflects the culture of the countryside."),
        PedagogicalVocabulary("vocab-u4-19", 4, "painting", "noun", "/ˈpeɪntɪŋ/", "bức tranh sơn dầu/màu", "This oil painting was painted in the 19th century."),
        PedagogicalVocabulary("vocab-u4-20", 4, "drawing", "noun", "/ˈdrɔːɪŋ/", "bức vẽ chì/mực", "His pencil drawings look very realistic."),
        PedagogicalVocabulary("vocab-u4-21", 4, "sculpture", "noun", "/ˈskʌlptʃə/", "tác phẩm điêu khắc", "There are many ancient sculptures in the museum."),
        PedagogicalVocabulary("vocab-u4-22", 4, "perform", "verb", "/pəˈfɔːm/", "biểu diễn", "The artists will perform traditional dances tonight."),
        PedagogicalVocabulary("vocab-u4-23", 4, "originate", "verb", "/əˈrɪdʒɪneɪt/", "bắt nguồn từ", "Water puppetry originated in northern Viet Nam."),
        PedagogicalVocabulary("vocab-u4-24", 4, "photography", "noun", "/fəˈtɒɡrəfi/", "nghệ thuật nhiếp ảnh", "Photography is her biggest passion."),
        PedagogicalVocabulary("vocab-u4-25", 4, "camera", "noun", "/ˈkæmrə/", "máy ảnh", "He brought his new digital camera to the exhibition."),
        PedagogicalVocabulary("vocab-u5-1", 5, "ingredient", "noun", "/ɪnˈɡriːdiənt/", "nguyên liệu", "The main ingredients of Pho are broth, noodles, and beef."),
        PedagogicalVocabulary("vocab-u5-2", 5, "omelette", "noun", "/ˈɒmlət/", "món trứng cuộn/trứng tráng", "I often make an omelette for breakfast."),
        PedagogicalVocabulary("vocab-u5-3", 5, "turmeric", "noun", "/ˈtɜːmərɪk/", "củ nghệ", "Turmeric gives the soup a beautiful yellow colour."),
        PedagogicalVocabulary("vocab-u5-4", 5, "noodles", "noun", "/ˈnuːdlz/", "mì, bún, phở", "Rice noodles are used in many Vietnamese dishes."),
        PedagogicalVocabulary("vocab-u5-5", 5, "broth", "noun", "/brɒθ/", "nước dùng, nước lèo", "The broth for Pho is simmered for many hours."),
        PedagogicalVocabulary("vocab-u5-6", 5, "tofu", "noun", "/ˈtəʊfuː/", "đậu phụ", "Fried tofu with tomato sauce is delicious."),
        PedagogicalVocabulary("vocab-u5-7", 5, "pork", "noun", "/pɔːk/", "thịt lợn", "We need half a kilo of pork for dinner."),
        PedagogicalVocabulary("vocab-u5-8", 5, "beef", "noun", "/biːf/", "thịt bò", "Beef noodle soup is very popular across Viet Nam."),
        PedagogicalVocabulary("vocab-u5-9", 5, "chicken", "noun", "/ˈtʃɪkɪn/", "thịt gà", "Chicken soup is good for recovering from a cold."),
        PedagogicalVocabulary("vocab-u5-10", 5, "mineral water", "noun", "/ˈmɪnərəl ˈwɔːtə/", "nước khoáng", "Would you like a bottle of mineral water?"),
        PedagogicalVocabulary("vocab-u5-11", 5, "lemonade", "noun", "/ˌleməˈneɪd/", "nước chanh", "A glass of cool lemonade is refreshing in summer."),
        PedagogicalVocabulary("vocab-u5-12", 5, "green tea", "noun", "/ɡriːn tiː/", "trà xanh", "Green tea is rich in healthy antioxidants."),
        PedagogicalVocabulary("vocab-u5-13", 5, "recipe", "noun", "/ˈresəpi/", "công thức nấu ăn", "Follow this recipe to make tasty spring rolls."),
        PedagogicalVocabulary("vocab-u5-14", 5, "delicious", "adj", "/dɪˈlɪʃəs/", "thơm ngon, ngon miệng", "This traditional Vietnamese food is really delicious."),
        PedagogicalVocabulary("vocab-u5-15", 5, "taste", "verb", "/teɪst/", "nếm, có vị", "Taste the soup to see if it needs more pepper."),
        PedagogicalVocabulary("vocab-u5-16", 5, "salt", "noun", "/sɔːlt/", "muối ăn", "Add a pinch of salt to the boiling water."),
        PedagogicalVocabulary("vocab-u5-17", 5, "pepper", "noun", "/ˈpepə/", "hạt tiêu", "Sprinkle some black pepper on the omelette."),
        PedagogicalVocabulary("vocab-u5-18", 5, "butter", "noun", "/ˈbʌtə/", "bơ", "Melt the butter in a pan over medium heat."),
        PedagogicalVocabulary("vocab-u5-19", 5, "flour", "noun", "/ˈflaʊə/", "bột mì", "Mix the wheat flour with warm milk and eggs."),
        PedagogicalVocabulary("vocab-u5-20", 5, "onion", "noun", "/ˈʌnjən/", "hành tây", "Chop the onion finely before frying."),
        PedagogicalVocabulary("vocab-u5-21", 5, "sauce", "noun", "/sɔːs/", "nước sốt, nước chấm", "Fish sauce is an essential ingredient in Vietnamese cooking."),
        PedagogicalVocabulary("vocab-u5-22", 5, "sugar", "noun", "/ˈʃʊɡə/", "đường", "Too much sugar is bad for your teeth."),
        PedagogicalVocabulary("vocab-u5-23", 5, "pancake", "noun", "/ˈpænkeɪk/", "bánh xèo, bánh kếp", "Vietnamese crispy pancakes are served with fresh herbs."),
        PedagogicalVocabulary("vocab-u5-24", 5, "spring rolls", "noun", "/sprɪŋ rəʊlz/", "nem rán, chả giò", "Spring rolls are crispy and flavorful."),
        PedagogicalVocabulary("vocab-u5-25", 5, "shrimp", "noun", "/ʃrɪmp/", "con tôm", "Fresh shrimps make the vegetable soup sweet."),
        PedagogicalVocabulary("vocab-u6-1", 6, "school facilities", "noun", "/skuːl fəˈsɪlətiz/", "cơ sở vật chất của trường", "Our school has modern and well-equipped facilities."),
        PedagogicalVocabulary("vocab-u6-2", 6, "computer room", "noun", "/kəmˈpjuːtə ruːm/", "phòng tin học máy tính", "We learn how to write code in the computer room."),
        PedagogicalVocabulary("vocab-u6-3", 6, "school library", "noun", "/skuːl ˈlaɪbrəri/", "thư viện trường", "Students borrow interesting science books from the school library."),
        PedagogicalVocabulary("vocab-u6-4", 6, "school garden", "noun", "/skuːl ˈɡɑːdn/", "khu vườn trường", "We grow vegetables and flowers in the school garden."),
        PedagogicalVocabulary("vocab-u6-5", 6, "playground", "noun", "/ˈpleɪɡraʊnd/", "sân chơi", "Children play badminton on the school playground."),
        PedagogicalVocabulary("vocab-u6-6", 6, "science lab", "noun", "/ˈsaɪəns læb/", "phòng thí nghiệm khoa học", "We conduct biology experiments in the science lab."),
        PedagogicalVocabulary("vocab-u6-7", 6, "gym", "noun", "/dʒɪm/", "nhà thể chất, phòng tập", "Physical education lessons are held in the gym."),
        PedagogicalVocabulary("vocab-u6-8", 6, "classroom", "noun", "/ˈklɑːsruːm/", "phòng học", "The classroom is bright and comfortable."),
        PedagogicalVocabulary("vocab-u6-9", 6, "lower secondary school", "noun", "/ˈləʊə ˈsekəndri skuːl/", "trường trung học cơ sở", "She is studying at a lower secondary school in Hue."),
        PedagogicalVocabulary("vocab-u6-10", 6, "gifted", "adj", "/ˈɡɪftɪd/", "có năng khiếu, chuyên", "Binh Minh is a school for gifted students in the city."),
        PedagogicalVocabulary("vocab-u6-11", 6, "midterm", "noun", "/ˈmɪdtɜːm/", "giữa kỳ", "The midterm test covers all the units we have studied."),
        PedagogicalVocabulary("vocab-u6-12", 6, "entrance examination", "noun", "/ˈentrəns ɪɡˌzæmɪˈneɪʃn/", "kỳ thi tuyển sinh", "Students have to pass a strict entrance examination."),
        PedagogicalVocabulary("vocab-u6-13", 6, "outdoor activities", "noun", "/ˈaʊtdɔːr ækˈtɪvətiz/", "hoạt động ngoài trời", "Outdoor activities help students develop team spirit."),
        PedagogicalVocabulary("vocab-u6-14", 6, "well-known", "adj", "/ˌwel ˈnəʊn/", "nổi tiếng", "Quoc Hoc - Hue is a well-known school in Viet Nam."),
        PedagogicalVocabulary("vocab-u6-15", 6, "suburbs", "noun", "/ˈsʌbɜːbz/", "vùng ngoại ô", "Their school is located in the peaceful suburbs."),
        PedagogicalVocabulary("vocab-u6-16", 6, "private school", "noun", "/ˈpraɪvət skuːl/", "trường tư thục", "He attends an international private school in London."),
        PedagogicalVocabulary("vocab-u6-17", 6, "take part in", "verb", "/teɪk pɑːt ɪn/", "tham gia vào", "All students take part in sports day competitions."),
        PedagogicalVocabulary("vocab-u6-18", 6, "encourage", "verb", "/ɪnˈkʌrɪdʒ/", "khuyến khích, động viên", "Teachers encourage students to read more literature."),
        PedagogicalVocabulary("vocab-u6-19", 6, "final exam", "noun", "/ˈfaɪnl ɪɡˈzæm/", "kỳ thi cuối kỳ", "We are reviewing our lessons for the final exam."),
        PedagogicalVocabulary("vocab-u6-20", 6, "intelligent", "adj", "/ɪnˈtelɪdʒənt/", "thông minh", "The students here are very intelligent and hard-working."),
        PedagogicalVocabulary("vocab-u6-21", 6, "founded", "adj", "/ˈfaʊndɪd/", "được thành lập", "Quoc Hoc - Hue was founded in 1896."),
        PedagogicalVocabulary("vocab-u6-22", 6, "historic", "adj", "/hɪˈstɒrɪk/", "mang tính lịch sử", "Chu Van An is one of the historic schools in Ha Noi."),
        PedagogicalVocabulary("vocab-u6-23", 6, "examination", "noun", "/ɪɡˌzæmɪˈneɪʃn/", "kỳ thi, bài kiểm tra", "Prepare carefully for your term examination."),
        PedagogicalVocabulary("vocab-u6-24", 6, "surround", "verb", "/səˈraʊnd/", "bao quanh, vây quanh", "Green trees surround the school campus."),
        PedagogicalVocabulary("vocab-u6-25", 6, "laboratory", "noun", "/ləˈbɒrətri/", "phòng thí nghiệm", "The chemistry laboratory has safe protective gear."),
        PedagogicalVocabulary("vocab-u7-1", 7, "traffic jam", "noun", "/ˈtræfɪk dʒæm/", "tắc nghẽn giao thông", "Avoid travelling in rush hour to not get stuck in a traffic jam."),
        PedagogicalVocabulary("vocab-u7-2", 7, "seatbelt", "noun", "/ˈsiːtbelt/", "dây an toàn", "Always fasten your seatbelt when driving a car."),
        PedagogicalVocabulary("vocab-u7-3", 7, "pedestrian", "noun", "/pəˈdestriən/", "người đi bộ", "Pedestrians should use the zebra crossing to cross the street."),
        PedagogicalVocabulary("vocab-u7-4", 7, "pavement", "noun", "/ˈpeɪvmənt/", "vỉa hè", "Walk on the pavement instead of on the road."),
        PedagogicalVocabulary("vocab-u7-5", 7, "helmet", "noun", "/ˈhelmɪt/", "mũ bảo hiểm", "Always wear a crash helmet when riding a motorbike."),
        PedagogicalVocabulary("vocab-u7-6", 7, "road sign", "noun", "/rəʊd saɪn/", "biển báo giao thông", "Road signs provide essential safety warnings."),
        PedagogicalVocabulary("vocab-u7-7", 7, "zebra crossing", "noun", "/ˌzebrə ˈkrɒsɪŋ/", "vạch qua đường", "Stop and wait at the zebra crossing for pedestrians."),
        PedagogicalVocabulary("vocab-u7-8", 7, "traffic light", "noun", "/ˈtræfɪk laɪt/", "đèn tín hiệu giao thông", "You must stop when the traffic light turns red."),
        PedagogicalVocabulary("vocab-u7-9", 7, "vehicle", "noun", "/ˈviːəkl/", "phương tiện giao thông", "Motorbikes and buses are common road vehicles."),
        PedagogicalVocabulary("vocab-u7-10", 7, "rush hour", "noun", "/rʌʃ ˈaʊə/", "giờ cao điểm", "Streets become crowded during morning rush hour."),
        PedagogicalVocabulary("vocab-u7-11", 7, "fine", "noun", "/faɪn/", "tiền phạt", "You may have to pay a fine for breaking traffic laws."),
        PedagogicalVocabulary("vocab-u7-12", 7, "obey", "verb", "/əˈbeɪ/", "chấp hành, tuân thủ", "Drivers must obey traffic signs and speed limits."),
        PedagogicalVocabulary("vocab-u7-13", 7, "traffic rule", "noun", "/ˈtræfɪk ruːl/", "luật giao thông", "Learning traffic rules helps prevent road accidents."),
        PedagogicalVocabulary("vocab-u7-14", 7, "safety", "noun", "/ˈseɪfti/", "sự an toàn", "Road safety is of primary importance for students."),
        PedagogicalVocabulary("vocab-u7-15", 7, "safe", "adj", "/seɪf/", "an toàn", "Is it safe to ride your bicycle at night?"),
        PedagogicalVocabulary("vocab-u7-16", 7, "careful", "adj", "/ˈkeəfl/", "cẩn thận", "Be careful when crossing a busy junction."),
        PedagogicalVocabulary("vocab-u7-17", 7, "cross", "verb", "/krɒs/", "băng qua", "Look both ways before you cross the street."),
        PedagogicalVocabulary("vocab-u7-18", 7, "cycle lane", "noun", "/ˈsaɪkl leɪn/", "làn đường xe đạp", "Ride your bicycle inside the dedicated cycle lane."),
        PedagogicalVocabulary("vocab-u7-19", 7, "passenger", "noun", "/ˈpæsɪndʒə/", "hành khách", "All bus passengers should hold on tight."),
        PedagogicalVocabulary("vocab-u7-20", 7, "roof", "noun", "/ruːf/", "nóc xe, mái", "Do not carry luggage on the vehicle roof."),
        PedagogicalVocabulary("vocab-u7-21", 7, "handlebars", "noun", "/ˈhændlbɑːz/", "tay lái ghi-đông", "Keep both hands on the handlebars while riding."),
        PedagogicalVocabulary("vocab-u7-22", 7, "train", "noun", "/treɪn/", "tàu hỏa, xe lửa", "Travelling by passenger train is comfortable and safe."),
        PedagogicalVocabulary("vocab-u7-23", 7, "drive", "verb", "/draɪv/", "lái xe", "You must not drive when feeling sleepy."),
        PedagogicalVocabulary("vocab-u7-24", 7, "lane", "noun", "/leɪn/", "làn đường", "Stay in your proper lane when turning."),
        PedagogicalVocabulary("vocab-u7-25", 7, "motorbike", "noun", "/ˈməʊtəbaɪk/", "xe máy", "Many commuters ride a motorbike to work."),
        PedagogicalVocabulary("vocab-u8-1", 8, "film", "noun", "/fɪlm/", "bộ phim", "We watched an exciting action film last night."),
        PedagogicalVocabulary("vocab-u8-2", 8, "comedy", "noun", "/ˈkɒmədi/", "phim hài kịch", "We laughed so hard watching this comedy."),
        PedagogicalVocabulary("vocab-u8-3", 8, "horror", "noun", "/ˈhɒrə/", "phim kinh dị", "Do not watch this horror film alone at night."),
        PedagogicalVocabulary("vocab-u8-4", 8, "documentary", "noun", "/ˌdɒkjuˈmentri/", "phim tài liệu", "This nature documentary shows wildlife in Africa."),
        PedagogicalVocabulary("vocab-u8-5", 8, "science fiction", "noun", "/ˌsaɪəns ˈfɪkʃn/", "phim khoa học viễn tưởng", "Science fiction films explore futuristic worlds."),
        PedagogicalVocabulary("vocab-u8-6", 8, "fantasy", "noun", "/ˈfæntəsi/", "phim giả tưởng", "Harry Potter is a world-famous fantasy story."),
        PedagogicalVocabulary("vocab-u8-7", 8, "actor", "noun", "/ˈæktə/", "nam diễn viên", "He is a talented dramatic actor."),
        PedagogicalVocabulary("vocab-u8-8", 8, "director", "noun", "/dəˈrektə/", "đạo diễn", "James Cameron is a legendary Hollywood film director."),
        PedagogicalVocabulary("vocab-u8-9", 8, "stars", "verb", "/stɑːz/", "đóng vai chính", "The film stars famous international actors."),
        PedagogicalVocabulary("vocab-u8-10", 8, "cinema", "noun", "/ˈsɪnəmə/", "rạp chiếu phim", "Let's go to the cinema to watch the premiere tonight."),
        PedagogicalVocabulary("vocab-u8-11", 8, "story", "noun", "/ˈstɔːri/", "cốt truyện, câu chuyện", "The movie tells an inspiring love story."),
        PedagogicalVocabulary("vocab-u8-12", 8, "reviews", "noun", "/rɪˈvjuːz/", "những bài đánh giá", "The new cinema release received excellent reviews."),
        PedagogicalVocabulary("vocab-u8-13", 8, "funny", "adj", "/ˈfʌni/", "buồn cười, hài hước", "The main character has a funny face."),
        PedagogicalVocabulary("vocab-u8-14", 8, "interesting", "adj", "/ˈɪntrəstɪŋ/", "thú vị, hấp dẫn", "The plot of this mystery film is very interesting."),
        PedagogicalVocabulary("vocab-u8-15", 8, "moving", "adj", "/ˈmuːvɪŋ/", "cảm động", "The emotional ending was very moving."),
        PedagogicalVocabulary("vocab-u8-16", 8, "boring", "adj", "/ˈbɔːrɪŋ/", "nhàm chán", "The film was boring and too long."),
        PedagogicalVocabulary("vocab-u8-17", 8, "frightening", "adj", "/ˈfraɪtnɪŋ/", "kinh hoàng", "The frightening ghost scenes made me close my eyes."),
        PedagogicalVocabulary("vocab-u8-18", 8, "shocking", "adj", "/ˈʃɒkɪŋ/", "gây sốc, kinh ngạc", "The plot twist at the climax was shocking."),
        PedagogicalVocabulary("vocab-u8-19", 8, "violent", "adj", "/ˈvaɪələnt/", "bạo lực", "Children should not watch violent action movies."),
        PedagogicalVocabulary("vocab-u8-20", 8, "confusing", "adj", "/kənˈfjuːzɪŋ/", "khó hiểu, rối rắm", "The non-linear timeline in this movie was confusing."),
        PedagogicalVocabulary("vocab-u8-21", 8, "gripping", "adj", "/ˈɡrɪpɪŋ/", "hấp dẫn, kịch tính", "The detective film has a gripping plot."),
        PedagogicalVocabulary("vocab-u8-22", 8, "scary", "adj", "/ˈskeəri/", "đáng sợ, rùng rợn", "The strange sound in the dark was really scary."),
        PedagogicalVocabulary("vocab-u8-23", 8, "recommend", "verb", "/ˌrekəˈmend/", "khuyên xem, giới thiệu", "I highly recommend this science fiction movie."),
        PedagogicalVocabulary("vocab-u8-24", 8, "favourite", "adj", "/ˈfeɪvərɪt/", "yêu thích nhất", "What is your all-time favourite film genre?"),
        PedagogicalVocabulary("vocab-u8-25", 8, "ending", "noun", "/ˈendɪŋ/", "phần kết thúc", "The unexpected ending surprised everyone."),
        PedagogicalVocabulary("vocab-u9-1", 9, "festival", "noun", "/ˈfestɪvl/", "lễ hội", "The Tulip Festival takes place in the Netherlands every spring."),
        PedagogicalVocabulary("vocab-u9-2", 9, "celebrate", "verb", "/ˈselɪbreɪt/", "kỷ niệm, ăn mừng", "People celebrate Easter with decorated chocolate eggs."),
        PedagogicalVocabulary("vocab-u9-3", 9, "celebration", "noun", "/ˌselɪˈbreɪʃn/", "lễ kỷ niệm", "The New Year celebration ended with dazzling fireworks."),
        PedagogicalVocabulary("vocab-u9-4", 9, "easter", "noun", "/ˈiːstə/", "Lễ Phục Sinh", "Children search for hidden chocolate eggs on Easter morning."),
        PedagogicalVocabulary("vocab-u9-5", 9, "tulip", "noun", "/ˈtjuːlɪp/", "hoa tulip", "Fields of blooming tulips attract visitors from all over."),
        PedagogicalVocabulary("vocab-u9-6", 9, "thanksgiving", "noun", "/ˌθæŋksˈɡɪvɪŋ/", "Lễ Tạ Ơn", "On Thanksgiving, Americans enjoy roasted turkey."),
        PedagogicalVocabulary("vocab-u9-7", 9, "halloween", "noun", "/ˌhæləʊˈiːn/", "Lễ hội Halloween", "People carve lanterns out of pumpkins for Halloween."),
        PedagogicalVocabulary("vocab-u9-8", 9, "christmas", "noun", "/ˈkrɪsməs/", "Lễ Giáng Sinh", "Families decorate Christmas trees with colorful ornaments."),
        PedagogicalVocabulary("vocab-u9-9", 9, "parade", "noun", "/pəˈreɪd/", "cuộc diễu hành", "People dress in colourful costumes during the street parade."),
        PedagogicalVocabulary("vocab-u9-10", 9, "costume", "noun", "/ˈkɒstjuːm/", "trang phục hóa trang", "Performers wear traditional silk costumes in the parade."),
        PedagogicalVocabulary("vocab-u9-11", 9, "costumes", "noun", "/ˈkɒstjuːmz/", "các bộ trang phục", "Children wore spooky costumes on Halloween night."),
        PedagogicalVocabulary("vocab-u9-12", 9, "dancers", "noun", "/ˈdɑːnsəz/", "những vũ công", "Talented dancers moved rhythmically with the music."),
        PedagogicalVocabulary("vocab-u9-13", 9, "folk dance", "noun", "/fəʊk dɑːns/", "điệu múa dân gian", "Dancers perform traditional folk dances to drum music."),
        PedagogicalVocabulary("vocab-u9-14", 9, "fireworks", "noun", "/ˈfaɪəwɜːks/", "pháo hoa", "Colourful fireworks lit up the midnight sky."),
        PedagogicalVocabulary("vocab-u9-15", 9, "feast", "noun", "/fiːst/", "bữa tiệc thịnh soạn", "Families gather to share a Thanksgiving feast."),
        PedagogicalVocabulary("vocab-u9-16", 9, "symbol", "noun", "/ˈsɪmbl/", "biểu tượng", "The red tulip is a famous symbol of Holland."),
        PedagogicalVocabulary("vocab-u9-17", 9, "autumn", "noun", "/ˈɔːtəm/", "mùa thu", "The Mid-Autumn festival brings joy to Vietnamese children."),
        PedagogicalVocabulary("vocab-u9-18", 9, "moon", "noun", "/muːn/", "mặt trăng", "Children carry lanterns and gaze at the bright full moon."),
        PedagogicalVocabulary("vocab-u9-19", 9, "candy", "noun", "/ˈkændi/", "kẹo ngọt", "Kids ask for sweet candy on Halloween night."),
        PedagogicalVocabulary("vocab-u9-20", 9, "turkey", "noun", "/ˈtɜːki/", "gà tây", "Roast turkey is the traditional dish on Thanksgiving."),
        PedagogicalVocabulary("vocab-u9-21", 9, "tradition", "noun", "/trəˈdɪʃn/", "truyền thống", "Eating mooncakes is a festive tradition at Mid-Autumn."),
        PedagogicalVocabulary("vocab-u9-22", 9, "carnival", "noun", "/ˈkɑːnɪvl/", "lễ hội hóa trang", "The Rio Carnival is the most famous carnival in the world."),
        PedagogicalVocabulary("vocab-u9-23", 9, "twins", "noun", "/twɪnz/", "cặp song sinh", "The Twins Day Festival celebrates identical twins."),
        PedagogicalVocabulary("vocab-u9-24", 9, "eggs", "noun", "/eɡz/", "những quả trứng", "Children paint colourful designs on Easter eggs."),
        PedagogicalVocabulary("vocab-u9-25", 9, "festive", "adj", "/ˈfestɪv/", "thuộc lễ hội, náo nức", "The town has a wonderful festive atmosphere during Tet."),
        PedagogicalVocabulary("vocab-u10-1", 10, "energy", "noun", "/ˈenədʒi/", "năng lượng", "We need energy for electricity, heating and transport."),
        PedagogicalVocabulary("vocab-u10-2", 10, "sources", "noun", "/ˈsɔːsɪz/", "các nguồn", "Wind and sun are inexhaustible energy sources."),
        PedagogicalVocabulary("vocab-u10-3", 10, "renewable", "adj", "/rɪˈnjuːəbl/", "tái tạo được", "Solar and wind are renewable sources of energy."),
        PedagogicalVocabulary("vocab-u10-4", 10, "solar", "adj", "/ˈsəʊlə/", "thuộc mặt trời", "Solar power is clean and safe for our earth."),
        PedagogicalVocabulary("vocab-u10-5", 10, "panels", "noun", "/ˈpænlz/", "những tấm pin", "Rooftop solar panels produce domestic electricity."),
        PedagogicalVocabulary("vocab-u10-6", 10, "wind", "noun", "/wɪnd/", "gió", "Wind power is an eco-friendly source of energy."),
        PedagogicalVocabulary("vocab-u10-7", 10, "coal", "noun", "/kəʊl/", "than đá", "Burning coal causes severe atmospheric air pollution."),
        PedagogicalVocabulary("vocab-u10-8", 10, "natural", "adj", "/ˈnætʃrəl/", "tự nhiên", "Natural gas is a non-renewable fossil fuel."),
        PedagogicalVocabulary("vocab-u10-9", 10, "hydro", "noun", "/ˈhaɪdrəʊ/", "thủy điện", "Hydro power stations generate electricity from water flow."),
        PedagogicalVocabulary("vocab-u10-10", 10, "nuclear", "adj", "/ˈnjuːkliə/", "hạt nhân", "Nuclear power stations generate massive amounts of energy."),
        PedagogicalVocabulary("vocab-u10-11", 10, "electricity", "noun", "/ɪˌlekˈtrɪsəti/", "điện năng", "Turn off household electrical appliances to save electricity."),
        PedagogicalVocabulary("vocab-u10-12", 10, "environment", "noun", "/ɪnˈvaɪrənmənt/", "môi trường", "Protecting the global environment is everyone's duty."),
        PedagogicalVocabulary("vocab-u10-13", 10, "cheap", "adj", "/tʃiːp/", "rẻ, tiết kiệm chi phí", "Solar electricity will become cheap and popular soon."),
        PedagogicalVocabulary("vocab-u10-14", 10, "expensive", "adj", "/ɪkˈspensɪv/", "đắt đỏ, tốn kém", "Installing rooftop solar panels is expensive initially."),
        PedagogicalVocabulary("vocab-u10-15", 10, "safe", "adj", "/seɪf/", "an toàn", "Renewable energy is safe for human communities."),
        PedagogicalVocabulary("vocab-u10-16", 10, "dangerous", "adj", "/ˈdeɪndʒərəs/", "nguy hiểm", "Radiation leaks from nuclear accidents are extremely dangerous."),
        PedagogicalVocabulary("vocab-u10-17", 10, "bulbs", "noun", "/bʌlbz/", "những bóng đèn", "Use low-energy light bulbs to save electricity."),
        PedagogicalVocabulary("vocab-u10-18", 10, "appliances", "noun", "/əˈplaɪənsɪz/", "thiết bị gia dụng", "Turn off electrical appliances when not in use."),
        PedagogicalVocabulary("vocab-u10-19", 10, "replace", "verb", "/rɪˈpleɪs/", "thay thế", "We should replace fossil fuels with renewable alternatives."),
        PedagogicalVocabulary("vocab-u10-20", 10, "power", "noun", "/ˈpaʊə/", "năng lượng, điện lực", "Solar and wind power are safe for the earth."),
        PedagogicalVocabulary("vocab-u10-21", 10, "heat", "noun", "/hiːt/", "nhiệt lượng, sức nóng", "Solar energy can heat swimming pool water."),
        PedagogicalVocabulary("vocab-u10-22", 10, "clean", "adj", "/kliːn/", "sạch sẽ, không ô nhiễm", "Green energy keeps our living environment clean."),
        PedagogicalVocabulary("vocab-u10-23", 10, "save", "verb", "/seɪv/", "tiết kiệm", "Save energy by walking instead of driving."),
        PedagogicalVocabulary("vocab-u10-24", 10, "produce", "verb", "/prəˈdjuːs/", "sản xuất, tạo ra", "Wind turbines produce large quantities of power."),
        PedagogicalVocabulary("vocab-u10-25", 10, "light", "noun", "/laɪt/", "ánh sáng, đèn", "Turn off the light when leaving your room."),
        PedagogicalVocabulary("vocab-u11-1", 11, "travel", "verb", "/ˈtrævl/", "đi lại, di chuyển", "People will travel smoothly between planets in the future."),
        PedagogicalVocabulary("vocab-u11-2", 11, "cars", "noun", "/kɑːz/", "những chiếc ô tô", "Driverless cars will navigate roads safely."),
        PedagogicalVocabulary("vocab-u11-3", 11, "safe", "adj", "/seɪf/", "an toàn", "Is automated flight travel safe for children?"),
        PedagogicalVocabulary("vocab-u11-4", 11, "hyperloop", "noun", "/ˈhaɪpəluːp/", "tàu siêu tốc ống chân không", "Hyperloop transports capsule passengers through vacuum tubes."),
        PedagogicalVocabulary("vocab-u11-5", 11, "flying", "adj", "/ˈflaɪɪŋ/", "biết bay", "Flying cars can avoid road congestion."),
        PedagogicalVocabulary("vocab-u11-6", 11, "fast", "adj", "/fɑːst/", "nhanh chóng", "Future trains will run at amazingly fast speeds."),
        PedagogicalVocabulary("vocab-u11-7", 11, "electricity", "noun", "/ɪˌlekˈtrɪsəti/", "điện năng", "Future vehicles will run on clean electricity."),
        PedagogicalVocabulary("vocab-u11-8", 11, "passengers", "noun", "/ˈpæsɪndʒəz/", "các hành khách", "Future automated vehicles safely transport many passengers."),
        PedagogicalVocabulary("vocab-u11-9", 11, "future", "noun", "/ˈfjuːtʃə/", "tương lai", "Travelling in the future will be green and eco-friendly."),
        PedagogicalVocabulary("vocab-u11-10", 11, "driverless", "adj", "/ˈdraɪvələs/", "không người lái", "Driverless cars will navigate streets safely without humans."),
        PedagogicalVocabulary("vocab-u11-11", 11, "traffic", "noun", "/ˈtræfɪk/", "giao thông", "New flying vehicles will avoid road traffic."),
        PedagogicalVocabulary("vocab-u11-12", 11, "friendly", "adj", "/ˈfrendli/", "thân thiện", "Eco-friendly vehicles do not pollute the air."),
        PedagogicalVocabulary("vocab-u11-13", 11, "teleporter", "noun", "/ˈtelɪpɔːtə/", "thiết bị dịch chuyển tức thời", "A teleporter sends people anywhere in the blink of an eye."),
        PedagogicalVocabulary("vocab-u11-14", 11, "solar", "adj", "/ˈsəʊlə/", "thuộc mặt trời", "Solar vehicles use photovoltaic roof cells."),
        PedagogicalVocabulary("vocab-u11-15", 11, "powered", "adj", "/ˈpaʊəd/", "chạy bằng năng lượng", "Solar-powered trains are clean and quiet."),
        PedagogicalVocabulary("vocab-u11-16", 11, "transport", "noun", "/ˈtrænspɔːt/", "giao thông vận tải", "Eco-friendly means of transport help reduce pollution."),
        PedagogicalVocabulary("vocab-u11-17", 11, "faster", "adj", "/ˈfɑːstə/", "nhanh hơn", "Future high-speed transit will be much faster."),
        PedagogicalVocabulary("vocab-u11-18", 11, "bamboo", "noun", "/ˌbæmˈbuː/", "cây tre", "The bamboo copter is a lightweight flying gadget."),
        PedagogicalVocabulary("vocab-u11-19", 11, "copter", "noun", "/ˈkɒptə/", "máy bay lên thẳng mini", "The bamboo-copter allows personal flying over heavy traffic."),
        PedagogicalVocabulary("vocab-u11-20", 11, "electric", "adj", "/ɪˈlektrɪk/", "chạy bằng điện", "Electric vehicles help reduce greenhouse gas emissions."),
        PedagogicalVocabulary("vocab-u11-21", 11, "autopilot", "noun", "/ˈɔːtəʊpaɪlət/", "chế độ lái tự động", "The autopilot system controls cruising speed and direction."),
        PedagogicalVocabulary("vocab-u11-22", 11, "petrol", "noun", "/ˈpetrəl/", "xăng dầu", "Future vehicles will run on clean electricity instead of petrol."),
        PedagogicalVocabulary("vocab-u11-23", 11, "convenient", "adj", "/kənˈviːniənt/", "thuận tiện, tiện lợi", "On-demand automated shuttles are extremely convenient."),
        PedagogicalVocabulary("vocab-u11-24", 11, "comfortable", "adj", "/ˈkʌmftəbl/", "thoải mái, tiện nghi", "The interior cabin of the new vehicle is very comfortable."),
        PedagogicalVocabulary("vocab-u11-25", 11, "speed", "noun", "/spiːd/", "tốc độ", "The bullet train cruises at breathtaking speed."),
        PedagogicalVocabulary("vocab-u12-1", 12, "country", "noun", "/ˈkʌntri/", "quốc gia, đất nước", "Australia is a fascinating English-speaking country."),
        PedagogicalVocabulary("vocab-u12-2", 12, "island", "noun", "/ˈaɪlənd/", "hòn đảo", "New Zealand consists of two scenic main islands."),
        PedagogicalVocabulary("vocab-u12-3", 12, "capital", "noun", "/ˈkæpɪtl/", "thủ đô", "Ottawa is the official capital city of Canada."),
        PedagogicalVocabulary("vocab-u12-4", 12, "city", "noun", "/ˈsɪti/", "thành phố", "London is a bustling international city."),
        PedagogicalVocabulary("vocab-u12-5", 12, "scotland", "noun", "/ˈskɒtlənd/", "xứ Scotland", "Scotland is famous for historic castles and bagpipes."),
        PedagogicalVocabulary("vocab-u12-6", 12, "attraction", "noun", "/əˈtrækʃn/", "điểm thu hút du khách", "Niagara Falls is a world-renowned natural attraction."),
        PedagogicalVocabulary("vocab-u12-7", 12, "tour", "noun", "/tʊə/", "chuyến tham quan", "We took a guided bus tour around London."),
        PedagogicalVocabulary("vocab-u12-8", 12, "ancient", "adj", "/ˈeɪnʃənt/", "cổ xưa, cổ kính", "Stonehenge is an ancient stone monument in southern England."),
        PedagogicalVocabulary("vocab-u12-9", 12, "culture", "noun", "/ˈkʌltʃə/", "văn hóa", "Explore the diverse cultures of English-speaking nations."),
        PedagogicalVocabulary("vocab-u12-10", 12, "palace", "noun", "/ˈpæləs/", "cung điện", "Buckingham Palace is the official London residence of the King."),
        PedagogicalVocabulary("vocab-u12-11", 12, "unique", "adj", "/juˈniːk/", "độc đáo, có một không hai", "Maori culture offers rich and unique heritage traditions."),
        PedagogicalVocabulary("vocab-u12-12", 12, "castle", "noun", "/ˈkɑːsl/", "lâu đài", "Edinburgh Castle towers majestically above the historic city."),
        PedagogicalVocabulary("vocab-u12-13", 12, "local", "adj", "/ˈləʊkl/", "địa phương", "Taste delicious local food in traditional pubs."),
        PedagogicalVocabulary("vocab-u12-14", 12, "native", "adj", "/ˈneɪtɪv/", "bản địa", "Kangaroos and koalas are native animals of Australia."),
        PedagogicalVocabulary("vocab-u12-15", 12, "scottish", "adj", "/ˈskɒtɪʃ/", "thuộc về Scotland", "Highland bagpipes are a proud Scottish cultural tradition."),
        PedagogicalVocabulary("vocab-u12-16", 12, "coastline", "noun", "/ˈkəʊstlaɪn/", "đường bờ biển", "Australia has a long and stunning ocean coastline."),
        PedagogicalVocabulary("vocab-u12-17", 12, "visitors", "noun", "/ˈvɪzɪtəz/", "du khách", "Millions of international visitors tour London museums each year."),
        PedagogicalVocabulary("vocab-u12-18", 12, "symbol", "noun", "/ˈsɪmbl/", "biểu tượng", "The red maple leaf is Canada's national symbol."),
        PedagogicalVocabulary("vocab-u12-19", 12, "tower", "noun", "/ˈtaʊə/", "tòa tháp", "Tower Bridge is one of London's most famous landmarks."),
        PedagogicalVocabulary("vocab-u12-20", 12, "river", "noun", "/ˈrɪvə/", "dòng sông", "A boat cruise along the River Thames is very relaxing."),
        PedagogicalVocabulary("vocab-u12-21", 12, "maori", "noun", "/ˈmaʊri/", "người Maori", "The Maori are the indigenous Polynesian people of New Zealand."),
        PedagogicalVocabulary("vocab-u12-22", 12, "amazing", "adj", "/əˈmeɪzɪŋ/", "tuyệt vời, kinh ngạc", "The panoramic view from the observation deck was amazing."),
        PedagogicalVocabulary("vocab-u12-23", 12, "famous", "adj", "/ˈfeɪməs/", "nổi tiếng", "Australia is famous for its natural wonders and wildlife."),
        PedagogicalVocabulary("vocab-u12-24", 12, "kangaroo", "noun", "/ˌkæŋɡəˈruː/", "chuột túi kangaroo", "Kangaroos hop gracefully across the Australian outback."),
        PedagogicalVocabulary("vocab-u12-25", 12, "boat", "noun", "/bəʊt/", "thuyền, tàu", "We took a boat ride down the scenic canal."),
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
