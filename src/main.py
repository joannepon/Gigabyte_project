import time
from parse_data import run_parsing_pipeline
from retrieve import load_chunks, GigabyteRetriever
from answer import format_answer_from_chunk

def ask_assistant(query, retriever, top_k=1, return_metrics=False):
    start_time = time.time()

    retrieved_items = retriever.retrieve(query, top_k=top_k)

    print("\n=== Retrieved Chunks ===")
    for i, item in enumerate(retrieved_items, 1):
        chunk = item["chunk"]
        print(f"[{i}] score={item['score']:.4f} | {chunk['key']} | {chunk['value']}")

    first_token_time = time.time()
    answer = format_answer_from_chunk(query, retrieved_items[0]["chunk"])
    end_time = time.time()

    print("\n=== Final Answer ===")
    print(answer)

    ttft = (first_token_time - start_time) * 1000
    token_count = len(answer.split())
    total_time = end_time - start_time
    tps = token_count / total_time if total_time > 0 else 0.0

    print("\n=== Metrics ===")
    print(f"TTFT: {ttft:.2f} ms")
    print(f"TPS: {tps:.2f} tokens/s")
    print(f"Output tokens: {token_count}")

    if return_metrics:
        return {
            "answer": answer,
            "ttft_ms": ttft,
            "tps": tps,
            "token_count": token_count,
            "retrieved_items": retrieved_items
        }

    return answer

def main():
    # parse raw text into json/chunks
    run_parsing_pipeline()

    # load retriever
    chunks = load_chunks()
    retriever = GigabyteRetriever(chunks)

    # demo queries
    ask_assistant("這台的 CPU 是什麼？", retriever)
    ask_assistant("Does it support Wi-Fi 7?", retriever)
    ask_assistant("右側有哪些連接埠？", retriever)
    ask_assistant("How much battery capacity does it have?", retriever)
    ask_assistant("Does it have Thunderbolt 5?", retriever)

if __name__ == "__main__":
    main()
