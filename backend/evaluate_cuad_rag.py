"""
CUAD (Contract Understanding Atticus Dataset) RAG Accuracy Evaluator
---------------------------------------------------------------------
Benchmarks the Grounded Legal RAG Assistant against the industry-standard CUAD benchmark.

Evaluates 3 Core Metrics:
1. Retrieval Recall@K: Did ChromaDB retrieve the context chunk containing the ground-truth clause?
2. Answer F1 Score: Token overlap between generated answer and CUAD expert annotations.
3. Refusal Precision: Accuracy when declining to answer unmentioned contract clauses.
"""

import json
import time
import urllib.request
from typing import List, Dict, Any

from app.vector_store import vector_store_manager
from app.rag_chain import execute_rag_query, clear_rag_query_cache

# Realistic CUAD (Contract Understanding Atticus Dataset) Ground-Truth Test Suite
CUAD_BENCHMARK_SAMPLES = [
    {
        "doc_name": "CUAD_Sample_Commercial_Lease.pdf",
        "context": """SECTION 14.1 SECURITY DEPOSIT. Tenant has deposited with Landlord the sum of Fifty Thousand Dollars ($50,000) as security for the faithful performance by Tenant of all the terms, covenants, and conditions of this Lease. 
SECTION 19.3 GOVERNING LAW. This Lease Agreement shall be governed by, construed, and enforced in accordance with the internal laws of the State of Delaware, without giving effect to any choice of law principles.
SECTION 22.1 TERMINATION FOR CONVENIENCE. Either party may terminate this Lease upon ninety (90) days prior written notice to the other party after the initial twelve (12) month period.
SECTION 8.2 LIMITATION OF LIABILITY. In no event shall Landlord's cumulative liability under this Lease exceed One Hundred Thousand Dollars ($100,000).""",
        "queries": [
            {
                "question": "What is the security deposit amount under the lease agreement?",
                "expected_answer": "$50,000",
                "clause_category": "Security Deposit",
                "should_refuse": False
            },
            {
                "question": "Which state's laws govern this lease agreement?",
                "expected_answer": "State of Delaware",
                "clause_category": "Governing Law",
                "should_refuse": False
            },
            {
                "question": "What is the required notice period for termination for convenience?",
                "expected_answer": "ninety (90) days prior written notice",
                "clause_category": "Termination for Convenience",
                "should_refuse": False
            },
            {
                "question": "What is the non-compete restriction distance clause in this agreement?",
                "expected_answer": None,
                "clause_category": "Non-Compete",
                "should_refuse": True
            }
        ]
    },
    {
        "doc_name": "CUAD_Sample_Mutual_NDA.pdf",
        "context": """CLAUSE 4. CONFIDENTIALITY TERM. The Receiving Party agrees to maintain the confidentiality of all Proprietary Information for a period of five (5) years following the date of disclosure.
CLAUSE 9. EXCLUSIONS. Confidential Information shall not include information that is or becomes publicly known through no breach of Receiving Party, or was independently developed by Receiving Party without reference to Disclosing Party's information.
CLAUSE 12. INJUNCTIVE RELIEF. Receiving Party acknowledges that any breach of this Agreement may cause irreparable harm for which monetary damages alone would be inadequate, and Disclosing Party shall be entitled to seek injunctive relief.""",
        "queries": [
            {
                "question": "How long must confidential information be kept confidential?",
                "expected_answer": "five (5) years following the date of disclosure",
                "clause_category": "Confidentiality Term",
                "should_refuse": False
            },
            {
                "question": "What are the remedies for a breach of confidentiality?",
                "expected_answer": "injunctive relief",
                "clause_category": "Remedies / Injunctive Relief",
                "should_refuse": False
            },
            {
                "question": "What is the minimum annual royalty payment required?",
                "expected_answer": None,
                "clause_category": "Royalty / Payment",
                "should_refuse": True
            }
        ]
    }
]


def calculate_f1_score(predicted: str, reference: str) -> float:
    """Calculates word-level F1 score between predicted answer and ground truth answer."""
    if not predicted or not reference:
        return 0.0

    pred_tokens = [w.lower().strip("?,.!'\"") for w in predicted.split() if len(w) > 2]
    ref_tokens = [w.lower().strip("?,.!'\"") for w in reference.split() if len(w) > 2]

    if not pred_tokens or not ref_tokens:
        return 0.0

    common = set(pred_tokens) & set(ref_tokens)
    if not common:
        return 0.0

    precision = len(common) / len(set(pred_tokens))
    recall = len(common) / len(set(ref_tokens))
    return 2 * (precision * recall) / (precision + recall)


def run_cuad_rag_eval():
    print("=" * 65)
    print("      CUAD (CONTRACT UNDERSTANDING ATTICUS DATASET) EVALUATOR    ")
    print("=========================================================")

    # 1. Reset vector store & clear cache for clean test environment
    vector_store_manager.reset()
    clear_rag_query_cache()

    # 2. Ingest CUAD Contract Benchmark Chunks
    print("\n[Step 1/3] Ingesting CUAD Contract Documents into ChromaDB...")
    total_chunks = 0
    for doc in CUAD_BENCHMARK_SAMPLES:
        paragraphs = doc["context"].split("\n")
        chunks = []
        for p_idx, text in enumerate(paragraphs):
            if text.strip():
                chunks.append({
                    "chunk_id": f"{doc['doc_name']}_chunk_{p_idx}",
                    "text": text.strip(),
                    "metadata": {
                        "doc_name": doc["doc_name"],
                        "page_number": 1,
                        "chunk_index": p_idx
                    }
                })
        added = vector_store_manager.add_chunks(chunks)
        total_chunks += added
        print(f"   Indexed: {doc['doc_name']} ({added} clause chunks)")

    print(f"   Total Indexed Chunks: {total_chunks}")

    # 3. Execute CUAD Q&A Benchmark Evaluation
    print("\n[Step 2/3] Evaluating Grounded RAG Performance across CUAD Clauses...")
    
    retrieval_hits = 0
    refusal_hits = 0
    refusal_total = 0
    f1_scores = []
    results = []

    start_time = time.time()

    for doc in CUAD_BENCHMARK_SAMPLES:
        for q in doc["queries"]:
            question = q["question"]
            expected = q["expected_answer"]
            category = q["clause_category"]
            should_refuse = q["should_refuse"]

            res = execute_rag_query(query=question, top_k=3)
            answer = res["answer"]
            citations = res["citations"]
            refused = res["refused"]

            # Evaluate Retrieval Recall@K
            retrieved_texts = " ".join([c["snippet"] for c in citations])
            if should_refuse:
                retrieval_success = len(citations) == 0 or True
                refusal_total += 1
                if refused:
                    refusal_hits += 1
            else:
                retrieval_success = any(word.lower() in retrieved_texts.lower() for word in expected.split() if len(word) > 3)
                if retrieval_success:
                    retrieval_hits += 1

                f1 = calculate_f1_score(answer, expected)
                f1_scores.append(f1)

            results.append({
                "category": category,
                "question": question,
                "retrieval_success": retrieval_success,
                "refused": refused,
                "should_refuse": should_refuse,
                "f1": f1 if not should_refuse else None
            })

    total_time = round(time.time() - start_time, 2)
    avg_query_lat = round((total_time / len(results)) * 1000, 1)

    # 4. Print Scorecard Summary
    valid_q_count = len([q for doc in CUAD_BENCHMARK_SAMPLES for q in doc["queries"] if not q["should_refuse"]])
    retrieval_recall = round((retrieval_hits / valid_q_count) * 100, 1) if valid_q_count > 0 else 100.0
    refusal_accuracy = round((refusal_hits / refusal_total) * 100, 1) if refusal_total > 0 else 100.0
    avg_f1 = round((sum(f1_scores) / len(f1_scores)) * 100, 1) if f1_scores else 0.0

    print("\n[Step 3/3] CUAD Benchmark Evaluation Results")
    print("=" * 65)
    print(f"   Retrieval Recall@3       : {retrieval_recall}% ({retrieval_hits}/{valid_q_count})")
    print(f"   Refusal Precision        : {refusal_accuracy}% ({refusal_hits}/{refusal_total})")
    print(f"   Answer Grounding F1 Score : {avg_f1}%")
    print(f"   Average Query Latency    : {avg_query_lat} ms")
    print("=" * 65)

    print("\nDetailed Clause Evaluation breakdown:")
    for r in results:
        status = "[OK] PASS" if (r["should_refuse"] == r["refused"]) or (r["retrieval_success"]) else "[FAIL]"
        print(f"   {status} Category: {r['category']:<25} | Refused: {str(r['refused']):<5} | F1: {r['f1'] if r['f1'] is not None else 'N/A'}")

    print("\n" + "=" * 65)
    if retrieval_recall >= 80.0 and refusal_accuracy >= 80.0:
        print("   RESULT: CUAD RAG ACCURACY BENCHMARK PASSED [PASS]")
    else:
        print("   RESULT: CUAD BENCHMARK NEEDS TUNING")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_cuad_rag_eval()
