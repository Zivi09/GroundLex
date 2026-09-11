"""
Comprehensive Unified Re-Verification Loop Script
--------------------------------------------------
Re-runs verification for all 6 tasks in a single unified execution.
"""
import sys
import json
import subprocess
from fastapi.testclient import TestClient

from app.main import app

def run_reverification_loop():
    client = TestClient(app)
    results = {}

    print("\n=======================================================")
    print("      UNIFIED EXPLICIT RE-VERIFICATION LOOP            ")
    print("=======================================================\n")

    # STEP 1: Verify Task 6 & Task 1 Ingestion Data
    print("[1/7] Testing Sample Ingestion & Active Index Registry (Task 6)...")
    res_load = client.post("/api/load-samples")
    assert res_load.status_code == 200
    res_docs = client.get("/api/documents")
    assert res_docs.status_code == 200
    docs = res_docs.json()
    assert len(docs) >= 3
    doc_names = [d["doc_name"] for d in docs]
    print(f"   Indexed Documents ({len(docs)}): {', '.join(doc_names)}")
    results["Task 6 (Active Index Registry)"] = "PASS"

    # STEP 2: Verify Task 1 (PDF Citations Tagging)
    print("\n[2/7] Testing PDF Grounded Citations (Task 1)...")
    payload = {"query": "What is the security deposit amount in the commercial lease agreement?", "top_k": 5}
    res_query = client.post("/api/query", json=payload)
    assert res_query.status_code == 200
    query_data = res_query.json()
    citations = query_data.get("citations", [])
    assert len(citations) > 0
    pdf_citations = [c for c in citations if c["doc_name"].endswith(".pdf")]
    assert len(pdf_citations) > 0
    print(f"   PDF Citations Found: {len(pdf_citations)}")
    print(f"   Sample Citation: {pdf_citations[0]['doc_name']} (Page {pdf_citations[0]['page_number']})")
    results["Task 1 (PDF Citations Tagging)"] = "PASS"

    # STEP 3: Verify Task 2 (Sources & Images Tabs Backend Data)
    print("\n[3/7] Testing Sources and Images Tabs Data (Task 2)...")
    conv_id = query_data.get("conversation_id")
    assert conv_id is not None
    assert "answer" in query_data
    assert "citations" in query_data
    print(f"   Conversation ID: {conv_id}")
    print(f"   Citations Available for Sources Tab: {len(citations)}")
    results["Task 2 (Sources & Images Tabs)"] = "PASS"

    # STEP 4: Verify Task 3 (Title Renaming & Server-Side Persistence)
    print("\n[4/7] Testing Conversation Title Inline Editing & Persistence (Task 3)...")
    new_title = "Lease Security Deposit Clause Review 2026"
    res_patch = client.patch(f"/api/conversations/{conv_id}", json={"title": new_title})
    assert res_patch.status_code == 200
    res_get = client.get(f"/api/conversations/{conv_id}")
    assert res_get.status_code == 200
    conv_detail = res_get.json()
    assert conv_detail["title"] == new_title
    print(f"   Title successfully renamed and persisted: '{conv_detail['title']}'")
    results["Task 3 (Title Renaming & Persistence)"] = "PASS"

    # STEP 5: Verify Task 4 (Left Search Panel & Search Endpoint)
    print("\n[5/7] Testing Conversation Search API (Task 4)...")
    res_search = client.get("/api/conversations/search?q=Lease")
    assert res_search.status_code == 200
    search_hits = res_search.json()
    assert len(search_hits) >= 1
    assert search_hits[0]["id"] == conv_id
    print(f"   Search returned {len(search_hits)} matching thread(s) for query 'Lease'")
    results["Task 4 (Search Panel Endpoint)"] = "PASS"

    # STEP 6: Verify Task 5 (Active Sidebar Route Alignment)
    print("\n[6/7] Testing Sidebar Navigation & Conversation Retrieval (Task 5)...")
    res_list = client.get("/api/conversations")
    assert res_list.status_code == 200
    print(f"   Saved Conversation Threads: {len(res_list.json())}")
    results["Task 5 (Sidebar Route Alignment)"] = "PASS"

    # STEP 7: Verify Frontend Production Build
    print("\n[7/7] Testing Frontend Compilation (npm run build)...")
    import os
    frontend_dir = "frontend" if os.path.exists("frontend") else "../frontend"
    build_proc = subprocess.run(["npm.cmd", "run", "build"], cwd=frontend_dir, capture_output=True, text=True, shell=True)
    assert build_proc.returncode == 0, f"Frontend build failed:\n{build_proc.stderr}"
    print("   Vite Production Build: PASSED (0 esbuild errors)")
    results["Frontend Build Verification"] = "PASS"

    # SUMMARY REPORT
    print("\n=======================================================")
    print("       RE-VERIFICATION LOOP EXECUTION SUMMARY          ")
    print("=======================================================")
    all_passed = True
    for item, status in results.items():
        print(f"  [OK] {item:<40}: {status}")
        if status != "PASS":
            all_passed = False

    print("=======================================================")
    if all_passed:
        print("  RESULT: ALL VERIFICATION CHECKS PASSED IN SAME RUN  ")
    else:
        print("  RESULT: VERIFICATION FAILED                         ")
    print("=======================================================\n")


if __name__ == "__main__":
    run_reverification_loop()
