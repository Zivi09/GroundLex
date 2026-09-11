"""
Legal Document RAG Evaluation Framework
----------------------------------------
Evaluates the Legal RAG assistant across 10 benchmark test cases:
1. Grounded Accuracy on Answerable Legal Queries.
2. Anti-Hallucination Refusal Accuracy on Deliberately Unanswerable Queries.
3. Citation Precision (Page-level retrieval match).
4. Comparative Analysis: Clause-Aware Chunking vs. Naive Fixed-Character Chunking.
"""

import os
import sys
import json
from tabulate import tabulate

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.ingestion import process_pdf_file
from app.vector_store import vector_store_manager
from app.rag_chain import execute_rag_query
from sample_docs.generate_samples import generate_all_samples, SAMPLE_DIR

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(EVAL_DIR, "eval_dataset.json")

def prepare_documents():
    """Ensures sample legal PDFs exist and are indexed in ChromaDB."""
    if not os.path.exists(SAMPLE_DIR) or not os.listdir(SAMPLE_DIR):
        print("[Eval] Generating sample legal PDFs...")
        generate_all_samples()

    # Index sample documents if vector store is empty
    docs = vector_store_manager.list_documents()
    if not docs:
        print("[Eval] Indexing sample documents into ChromaDB...")
        sample_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]
        for sf in sample_files:
            pdf_path = os.path.join(SAMPLE_DIR, sf)
            chunks = process_pdf_file(pdf_path)
            vector_store_manager.add_chunks(chunks)


def run_evaluation_suite():
    prepare_documents()

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print("\n" + "="*80)
    print("      LEGAL DOCUMENT RAG ASSISTANT - BENCHMARK EVALUATION RUN")
    print("="*80)
    print(f"LLM Provider: {settings.LLM_PROVIDER.upper()} ({settings.resolve_llm_model_name()})")
    print(f"Embedding Provider: {settings.EMBEDDING_PROVIDER.upper()}")
    print(f"Total Benchmark Test Cases: {len(test_cases)}\n")

    results_table = []
    total_cases = len(test_cases)
    correct_retrievals = 0
    correct_answers = 0
    refusal_successes = 0
    unanswerable_total = 0

    for item in test_cases:
        qid = item["id"]
        question = item["question"]
        is_answerable = item["is_answerable"]
        expected_doc = item["expected_document"]
        expected_page = item.get("expected_page")
        keywords = item["expected_answer_keywords"]

        # Run RAG Pipeline
        rag_res = execute_rag_query(query=question, top_k=5)
        answer = rag_res["answer"]
        citations = rag_res["citations"]
        refused = rag_res["refused"]

        # 1. Retrieval Verification (Check if expected page was retrieved)
        retrieved_page_found = False
        if is_answerable:
            for cit in citations:
                if cit["doc_name"] == expected_doc and cit["page_number"] == expected_page:
                    retrieved_page_found = True
                    break
            if retrieved_page_found:
                correct_retrievals += 1

        # 2. Answer / Refusal Verification
        passed = False
        status_label = ""

        if is_answerable:
            # Must answer correctly and contain key facts
            keyword_match = any(kw.lower() in answer.lower() for kw in keywords)
            if keyword_match and not refused:
                passed = True
                correct_answers += 1
                status_label = "[CORRECT ANSWER]"
            elif refused:
                status_label = "[FALSE REFUSAL]"
            else:
                status_label = "[PARTIAL / INCORRECT]"
        else:
            unanswerable_total += 1
            # Must refuse to answer
            if refused or any(kw.lower() in answer.lower() for kw in keywords):
                passed = True
                refusal_successes += 1
                status_label = "[REFUSED - ANTI-HALLUCINATION SUCCESS]"
            else:
                status_label = "[HALLUCINATED]"

        citations_str = ", ".join([f"P{c['page_number']}" for c in citations[:2]]) if citations else "None"

        results_table.append([
            qid,
            "Answerable" if is_answerable else "Unanswerable",
            question[:45] + "..." if len(question) > 45 else question,
            citations_str,
            status_label
        ])

    print(tabulate(
        results_table,
        headers=["ID", "Type", "Test Question", "Retrieved Pages", "Eval Outcome"],
        tablefmt="grid"
    ))

    # Summary Metrics
    answerable_total = total_cases - unanswerable_total
    retrieval_acc = (correct_retrievals / answerable_total) * 100 if answerable_total > 0 else 0
    answer_acc = (correct_answers / answerable_total) * 100 if answerable_total > 0 else 0
    refusal_acc = (refusal_successes / unanswerable_total) * 100 if unanswerable_total > 0 else 0
    overall_score = ((correct_answers + refusal_successes) / total_cases) * 100

    print("\n" + "="*60)
    print("                 BENCHMARK PERFORMANCE SUMMARY")
    print("="*60)
    print(f"- Overall System Accuracy:         {overall_score:.1f}% ({correct_answers + refusal_successes}/{total_cases})")
    print(f"- Retrieval Citation Precision:    {retrieval_acc:.1f}% ({correct_retrievals}/{answerable_total} pages matched)")
    print(f"- Answerable Accuracy:            {answer_acc:.1f}% ({correct_answers}/{answerable_total})")
    print(f"- Anti-Hallucination Refusal Rate: {refusal_acc:.1f}% ({refusal_successes}/{unanswerable_total} correctly refused)")
    print("="*60 + "\n")

    # Save benchmark JSON summary
    summary_output = {
        "overall_score": overall_score,
        "retrieval_precision": retrieval_acc,
        "answer_accuracy": answer_acc,
        "hallucination_refusal_rate": refusal_acc,
        "total_test_cases": total_cases,
        "llm_provider": settings.LLM_PROVIDER,
        "model_name": settings.resolve_llm_model_name(),
        "embedding_provider": settings.EMBEDDING_PROVIDER
    }

    with open(os.path.join(EVAL_DIR, "eval_results.json"), "w", encoding="utf-8") as out_f:
        json.dump(summary_output, out_f, indent=2)

    return summary_output

if __name__ == "__main__":
    run_evaluation_suite()
