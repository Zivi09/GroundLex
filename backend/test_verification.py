"""
Verification Test Script for Legal RAG Assistant API Endpoints
"""
import sys
import json
from fastapi.testclient import TestClient

from app.main import app

def run_tests():
    client = TestClient(app)
    print("--- Starting Backend API Verification Suite ---")

    # 1. Health Check
    res = client.get("/api/health")
    print(f"GET /api/health: {res.status_code}")
    assert res.status_code == 200
    health_data = res.json()
    print("Health Data:", health_data)

    # 2. Load Samples
    res = client.post("/api/load-samples")
    print(f"POST /api/load-samples: {res.status_code}")
    assert res.status_code == 200
    print("Sample Loading Result:", res.json()["message"])

    # 3. Query RAG Assistant
    payload = {
        "query": "What is the Security Deposit amount in the Commercial Lease Agreement?",
        "top_k": 5
    }
    res = client.post("/api/query", json=payload)
    print(f"POST /api/query: {res.status_code}")
    assert res.status_code == 200
    query_res = res.json()
    print("Query Answer:", query_res["answer"][:100] + "...")
    print("Citations Count:", len(query_res["citations"]))
    print("Conversation ID:", query_res["conversation_id"])
    conv_id = query_res["conversation_id"]

    # 4. List Conversations
    res = client.get("/api/conversations")
    print(f"GET /api/conversations: {res.status_code}")
    assert res.status_code == 200
    convs = res.json()
    print(f"Total Saved Conversations: {len(convs)}")

    # 5. Rename Conversation Title
    new_title = "Custom Renamed Security Deposit Query"
    res = client.patch(f"/api/conversations/{conv_id}", json={"title": new_title})
    print(f"PATCH /api/conversations/{conv_id}: {res.status_code}")
    assert res.status_code == 200
    updated_conv = res.json()
    assert updated_conv["title"] == new_title
    print("Successfully renamed title to:", updated_conv["title"])

    # 6. Search Conversations
    res = client.get(f"/api/conversations/search?q=Security")
    print(f"GET /api/conversations/search?q=Security: {res.status_code}")
    assert res.status_code == 200
    search_results = res.json()
    print(f"Search results for 'Security': {len(search_results)} match(es)")
    assert len(search_results) >= 1

    print("\n--- ALL BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_tests()
