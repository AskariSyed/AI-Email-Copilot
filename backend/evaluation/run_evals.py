import json
import sys
from pathlib import Path

# Ensure the backend directory is in the Python path to import app modules
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from evaluate_generation import evaluate_generation
from evaluate_retrieval import evaluate_retrieval

from app.core.database import SessionLocal
from app.models import EmailChunk, StyleProfile
from app.services.embeddings.manager import embed_texts
from app.services.llm.generator import generate_email_draft
from app.services.rag.retriever import retrieve_context


def load_dataset(file_path="dataset_format.json"):
    with open(Path(__file__).parent / file_path, "r") as f:
        return json.load(f)


def run_evaluation():
    dataset = load_dataset()
    db = SessionLocal()

    # Ensure there's a mock style profile for user 1 so generation doesn't crash
    if not db.query(StyleProfile).filter(StyleProfile.user_id == 1).first():
        try:
            profile = StyleProfile(user_id=1, profile_data={"formality": "Neutral"})
            db.add(profile)
            db.commit()
        except Exception:
            db.rollback()

    results = []

    agg_metrics = {
        "hit_rate": 0.0,
        "mrr": 0.0,
        "recall": 0.0,
        "context_relevance": 0.0,
        "groundedness": 0.0,
        "answer_relevance": 0.0,
        "concept_coverage": 0.0,
    }

    for item in dataset:
        print(f"Evaluating {item['id']}...")

        # 1. Retrieval Evaluation (Deterministic)
        query_embedding = embed_texts([item["input_text"]])[0]
        # Perform the semantic search to get chunk IDs
        db_results = (
            db.query(EmailChunk)
            .order_by(EmailChunk.embedding.cosine_distance(query_embedding))
            .limit(5)
            .all()
        )
        retrieved_items = [
            {"chunk_id": chunk.id, "distance": 0.0} for chunk in db_results
        ]

        retrieval_metrics = evaluate_retrieval(
            retrieved_items, item["expected_chunk_ids"]
        )

        # 2. Context Formulation
        context_data = retrieve_context(
            db, item["input_text"], item.get("sender"), item.get("thread_id")
        )
        full_context = "\n".join(
            context_data.get("similar_emails", [])
            + context_data.get("sender_history", [])
        )

        # Truncate context to prevent exceeding LLM judge token limits (Groq 8000 TPM limit)
        full_context = full_context[:3000]

        # 3. Generation Execution
        try:
            draft_response = generate_email_draft(
                db=db,
                user_id=1,
                incoming_email_text=item["input_text"],
                sender=item.get("sender"),
            )
            generated_text = draft_response["generated_body"]
        except Exception as e:
            print(f"Generation failed for {item['id']}: {e}")
            generated_text = ""

        # 4. Generation Evaluation (LLM-as-a-judge)
        if generated_text:
            generation_metrics = evaluate_generation(
                generated_text=generated_text,
                context_text=full_context,
                input_text=item["input_text"],
                expected_concepts=item["expected_concepts"],
            )
        else:
            generation_metrics = {
                "context_relevance": 0,
                "groundedness": 0,
                "answer_relevance": 0,
                "concept_coverage": 0,
                "reasoning": "Generation failed.",
            }

        # Accumulate
        item_result = {
            "id": item["id"],
            "retrieval": retrieval_metrics,
            "generation": generation_metrics,
        }
        results.append(item_result)

        agg_metrics["hit_rate"] += retrieval_metrics["hit_rate"]
        agg_metrics["mrr"] += retrieval_metrics["mrr"]
        agg_metrics["recall"] += retrieval_metrics["recall"]
        agg_metrics["context_relevance"] += generation_metrics["context_relevance"]
        agg_metrics["groundedness"] += generation_metrics["groundedness"]
        agg_metrics["answer_relevance"] += generation_metrics["answer_relevance"]
        agg_metrics["concept_coverage"] += generation_metrics["concept_coverage"]

    db.close()

    n = len(dataset)
    if n > 0:
        for k in agg_metrics:
            agg_metrics[k] /= n

    final_output = {"aggregate_metrics": agg_metrics, "details": results}

    out_file = Path(__file__).parent / "results.json"
    with open(out_file, "w") as f:
        json.dump(final_output, f, indent=2)

    print("\n--- Evaluation Complete ---")
    print(f"Hit Rate:          {agg_metrics['hit_rate']:.2f}")
    print(f"MRR:               {agg_metrics['mrr']:.2f}")
    print(f"Recall@K:          {agg_metrics['recall']:.2f}")
    print(f"Context Relevance: {agg_metrics['context_relevance']:.2f} / 5")
    print(f"Groundedness:      {agg_metrics['groundedness']:.2f} / 5")
    print(f"Answer Relevance:  {agg_metrics['answer_relevance']:.2f} / 5")
    print(f"Concept Coverage:  {agg_metrics['concept_coverage']:.2f} / 1")
    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    run_evaluation()
