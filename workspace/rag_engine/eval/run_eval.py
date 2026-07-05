"""
Chạy đánh giá offline chất lượng RAG. Import TRỰC TIẾP src/retriever.py
(không qua HTTP) để chạy nhanh và test đúng logic thật.

Chạy: cd rag_engine && python eval/run_eval.py
Yêu cầu: đã ingest dữ liệu (python src/ingestion/ingest.py).
"""
import sys
import os
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import retriever

TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_questions.yaml")


def run_search_profile_case(case: dict) -> dict:
    result = retriever.search_profile(keyword=case["keyword"], top_k=20)
    passed = result["total_found"] >= case.get("expect_min_results", 1)
    return {"id": case["id"], "type": "search_profile", "passed": passed, "total_found": result["total_found"]}


def run_profile_detail_case(case: dict) -> dict:
    result = retriever.search_profile_detail(
        archive_id=case["archive_id"], question=case["question"], top_k=case.get("top_k", 5)
    )
    expected = case.get("expected_contains", "")
    passed = result["found"] and any(expected.lower() in c["text"].lower() for c in result["chunks"])
    return {"id": case["id"], "type": "get_profile_detail", "passed": passed, "found_chunks": len(result.get("chunks", []))}


def main():
    with open(TEST_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    results = []
    for case in data.get("test_cases", []):
        try:
            if case["type"] == "search_profile":
                results.append(run_search_profile_case(case))
            elif case["type"] == "get_profile_detail":
                results.append(run_profile_detail_case(case))
        except Exception as e:
            results.append({"id": case["id"], "type": case["type"], "passed": False, "error": str(e)})

    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    print(f"\n{'='*50}")
    print(f"KẾT QUẢ ĐÁNH GIÁ: {passed}/{total} test case PASS")
    print(f"{'='*50}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['id']} ({r['type']}) - {r}")


if __name__ == "__main__":
    main()
