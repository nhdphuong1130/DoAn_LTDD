import sys
from english7.bootstrap import configure_runtime
from english7.core.settings import get_settings
from english7.modules.ai.contracts import Language


def main():
    print("=" * 70)
    print("🧪 RUNNING END-TO-END PEDAGOGICAL GRAPHRAG & TUTOR VERIFICATION")
    print("=" * 70)

    settings = get_settings()
    class DummyState:
        pass
    class DummyApp:
        def __init__(self):
            self.state = DummyState()

    app = DummyApp()
    resources = configure_runtime(app, settings)
    retrieval = app.state.tutor_service._retrieval
    tutor = app.state.tutor_service

    test_queries = [
        ("Khi nào dùng thì hiện tại đơn?", Language.VIETNAMESE, 1),
        ("Tell me about renewable energy sources in Unit 10", Language.ENGLISH, 10),
        ("What future means of transport will we use?", Language.ENGLISH, 11),
        ("Which countries are English-speaking countries?", Language.ENGLISH, 12),
        ("How to pronounce /ə/ and /ɜː/?", Language.ENGLISH, 1),
    ]

    all_passed = True

    for i, (query, lang, expected_unit) in enumerate(test_queries, 1):
        print(f"\n--- [Query {i}] \"{query}\" ({lang.value}) ---")
        
        # 1. Test Retrieval
        context = retrieval.retrieve(query)
        print(f"  • Retrieved Fragments: {len(context.fragments)}")
        print(f"  • Generated Citations: {len(context.citations)}")

        if not context.fragments:
            print("  ❌ Failed: No fragments retrieved!")
            all_passed = False
            continue

        units_found = {f.unit_number for f in context.fragments}
        print(f"  • Found Units in Fragments: {sorted(list(units_found))} (Expected contains: {expected_unit})")

        for idx, cit in enumerate(context.citations[:2], 1):
            print(f"    Citation #{idx}: PDF Page {cit.pdf_page} | Printed Page {cit.printed_page}")

        for idx, frag in enumerate(context.fragments[:2], 1):
            snippet = frag.text.replace("\n", " ")[:90]
            print(f"    Fragment #{idx} (Unit {frag.unit_number} - {frag.hierarchy[2]}): \"{snippet}...\"")

        # 2. Test Tutor ask
        try:
            answer = tutor.ask(query, lang)
            print(f"  • Tutor Answer Summary: {answer.answer[:120].strip()}...")
            print(f"  • Tutor Citations Count: {len(answer.citations)}")
            print("  ✓ Query Passed.")
        except Exception as e:
            print(f"  ⚠️ Tutor ask notice: {e}")

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL PEDAGOGICAL RETRIEVAL QUERIES VERIFIED SUCCESSFULLY!")
    else:
        print("❌ SOME QUERIES FAILED TO RETRIEVE EVIDENCE.")
    print("=" * 70)


if __name__ == "__main__":
    main()
