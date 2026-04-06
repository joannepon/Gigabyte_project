import json
import os
import sys
import time
from statistics import mean

# 讓 Python 能找到 src/ 裡的模組
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from parse_data import run_parsing_pipeline
from retrieve import load_chunks, GigabyteRetriever
from answer import format_answer_from_chunk
from config import MODEL_REPO_ID, MODEL_FILENAME

from huggingface_hub import hf_hub_download
from llama_cpp import Llama


EVAL_PATH = os.path.join(PROJECT_ROOT, "eval", "eval_questions.json")


def build_generation_prompt(query, retrieved_items):
    context = "\n\n".join([
        f"[Source {i+1}]\nField: {item['chunk']['key']}\nValue: {item['chunk']['value']}"
        for i, item in enumerate(retrieved_items)
    ])

    return f"""You are a hardware specification assistant.

Answer only based on the provided sources.
Do not add outside knowledge.
If the answer is not explicitly stated, say:
我無法根據提供的規格資料確認這個答案。

Sources:
{context}

Question:
{query}

Answer:
"""


def deterministic_ask(query, retriever, top_k=1, return_metrics=False):
    start_time = time.time()

    retrieved_items = retriever.retrieve(query, top_k=top_k)
    first_token_time = time.time()

    answer = format_answer_from_chunk(query, retrieved_items[0]["chunk"])
    end_time = time.time()

    ttft = (first_token_time - start_time) * 1000
    token_count = len(answer.split())
    total_time = end_time - start_time
    tps = token_count / total_time if total_time > 0 else 0.0

    if return_metrics:
        return {
            "answer": answer,
            "ttft_ms": ttft,
            "tps": tps,
            "token_count": token_count,
            "retrieved_items": retrieved_items
        }

    return answer


def llm_ask(query, retriever, llm, top_k=1, max_tokens=64, temperature=0.0, return_metrics=False):
    retrieved_items = retriever.retrieve(query, top_k=top_k)
    prompt = build_generation_prompt(query, retrieved_items)

    start_time = time.time()
    first_token_time = None
    full_response = ""

    stream = llm(
        prompt,
        stream=True,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["Question:", "Sources:"]
    )

    for chunk in stream:
        piece = chunk["choices"][0]["text"]
        if piece and first_token_time is None and piece.strip():
            first_token_time = time.time()
        full_response += piece

    end_time = time.time()

    ttft = (first_token_time - start_time) * 1000 if first_token_time else 0.0
    token_count = len(llm.tokenize(full_response.encode("utf-8")))
    total_time = end_time - start_time
    tps = token_count / total_time if total_time > 0 else 0.0

    result = {
        "answer": full_response.strip(),
        "ttft_ms": ttft,
        "tps": tps,
        "token_count": token_count,
        "retrieved_items": retrieved_items
    }

    if return_metrics:
        return result

    return full_response.strip()


def evaluate_retrieval_and_answer(eval_path, retriever):
    with open(eval_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total = len(samples)
    top1_hit = 0
    top3_hit = 0
    answer_hit = 0

    print("\n" + "=" * 50)
    print("Retrieval + Deterministic Answer Benchmark")
    print("=" * 50)

    for i, sample in enumerate(samples, 1):
        question = sample["question"]
        expected_key = sample["expected_key"]
        expected_keywords = sample["expected_keywords"]

        retrieved_items = retriever.retrieve(question, top_k=3)
        retrieved_keys = [item["chunk"]["key"] for item in retrieved_items]

        if len(retrieved_keys) > 0 and retrieved_keys[0] == expected_key:
            top1_hit += 1
        if expected_key in retrieved_keys[:3]:
            top3_hit += 1

        result = deterministic_ask(question, retriever, top_k=1, return_metrics=True)
        answer = result["answer"].lower()

        keyword_match = any(k.lower() in answer for k in expected_keywords)
        if keyword_match:
            answer_hit += 1

        print(f"\n[Sample {i}] {question}")
        print(f"Expected key: {expected_key}")
        print(f"Retrieved keys: {retrieved_keys}")
        print(f"Answer: {result['answer']}")
        print(f"Keyword match: {keyword_match}")

    metrics = {
        "total_samples": total,
        "top1_retrieval_accuracy": top1_hit / total,
        "top3_retrieval_accuracy": top3_hit / total,
        "answer_accuracy": answer_hit / total
    }

    print("\n" + "-" * 50)
    print("Deterministic Benchmark Summary")
    print("-" * 50)
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")

    return metrics


def evaluate_llm_latency(eval_path, retriever, llm):
    with open(eval_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    ttfts = []
    tpss = []

    print("\n" + "=" * 50)
    print("LLM Generation Benchmark (TTFT / TPS)")
    print("=" * 50)

    for i, sample in enumerate(samples, 1):
        question = sample["question"]
        result = llm_ask(question, retriever, llm, top_k=1, return_metrics=True)

        ttfts.append(result["ttft_ms"])
        tpss.append(result["tps"])

        print(f"\n[Sample {i}] {question}")
        print(f"TTFT: {result['ttft_ms']:.2f} ms")
        print(f"TPS: {result['tps']:.2f} tokens/s")
        print(f"Output tokens: {result['token_count']}")

    metrics = {
        "avg_ttft_ms": mean(ttfts),
        "avg_tps": mean(tpss),
        "min_ttft_ms": min(ttfts),
        "max_ttft_ms": max(ttfts)
    }

    print("\n" + "-" * 50)
    print("LLM Performance Summary")
    print("-" * 50)
    for k, v in metrics.items():
        print(f"{k}: {v:.2f}")

    return metrics


def main():
    print("Step 1: Parsing raw spec and building chunks...")
    run_parsing_pipeline()

    print("\nStep 2: Loading chunks and retriever...")
    chunks = load_chunks()
    retriever = GigabyteRetriever(chunks)

    print("\nStep 3: Running retrieval + deterministic answer benchmark...")
    retrieval_metrics = evaluate_retrieval_and_answer(EVAL_PATH, retriever)

    print("\nStep 4: Loading llama.cpp model for TTFT / TPS benchmark...")
    model_path = hf_hub_download(
        repo_id=MODEL_REPO_ID,
        filename=MODEL_FILENAME
    )

    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=-1,
        verbose=False
    )

    print("\nStep 5: Running LLM generation benchmark...")
    llm_metrics = evaluate_llm_latency(EVAL_PATH, retriever, llm)

    print("\n" + "=" * 50)
    print("Final Evaluation Summary")
    print("=" * 50)
    print("\nRetrieval / Deterministic Answer:")
    for k, v in retrieval_metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")

    print("\nLLM Generation:")
    for k, v in llm_metrics.items():
        print(f"{k}: {v:.2f}")


if __name__ == "__main__":
    main()
