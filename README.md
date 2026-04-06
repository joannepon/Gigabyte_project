# GIGABYTE AORUS MASTER 16 AM6H RAG System

## 1. Project Overview

This project implements a **pure Python Retrieval-Augmented Generation (RAG)** system for answering questions about the GIGABYTE AORUS MASTER 16 AM6H laptop specifications.

The system is designed under strict constraints:

- No LangChain / LlamaIndex  
- Pure Python implementation (parsing, chunking, retrieval, answering)  
- `uv` for environment and dependency management  
- `llama.cpp` for local inference  
- Supports **Traditional Chinese + English queries**  
- Designed to operate under a **4GB VRAM constraint**  

---

## 2. Model Choice and 4GB VRAM Constraint

### Embedding Model

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Reason:
- Supports both Traditional Chinese and English  
- Lightweight and efficient  
- Suitable for semantic retrieval  

---

### Generation Model

- `Qwen2.5-1.5B-Instruct`
- GGUF format
- Quantization: `q4_k_m`
- Inference: `llama.cpp`

Reason:
- Small model size suitable for constrained environments  
- Instruction-tuned for QA tasks  
- Quantization reduces memory usage  

---

### Design Strategy for 4GB VRAM

Instead of relying on large models, this system optimizes performance through:

- Structured data parsing  
- Field-level chunking  
- Query routing (field-aware retrieval)  
- Deterministic answer generation  

This significantly reduces the need for LLM usage.

---

### Key Insight

> Instead of scaling model size, the system improves efficiency through better retrieval and answer design, making it suitable for low-resource environments such as 4GB VRAM.


## 3. System Design

## Data Parsing

The product specification is treated as **structured data** rather than free-form text.  
The goal of this stage is to convert the raw specification into clean **key-value pairs**, so that each field can be retrieved and answered independently.

### Method

The parsing logic is implemented in pure Python and follows these steps:

1. Split the raw specification text into lines and remove empty lines  
2. Detect field headers using a regular expression (for example, lines ending with `:` or `：`)  
3. Group all following lines as the value of that field until the next field header appears  
4. Normalize whitespace and formatting into a clean single-line value  
5. Apply post-processing rules to handle edge cases such as:
   - merging nested port fields into `連接埠-Left Side` and `連接埠-Right Side`
   - separating incorrectly merged fields such as `變壓器` and `尺寸`
   - removing empty or redundant entries

### Output Format

The parsed result is stored as structured JSON:

```json
{
  "key": "中央處理器",
  "value": "Intel® Core™ Ultra 9 Processor 275HX (36MB cache, up to 5.4 GHz, 24 cores, 24 threads)"
}```

### Retrieval and Generation

### Vector Index and Retrieval

To enable efficient retrieval, the system converts each chunk into embeddings using a multilingual SentenceTransformer model.

- Model: `paraphrase-multilingual-MiniLM-L12-v2`
- Each chunk is encoded into a dense vector
- All vectors are stored in a FAISS index (`IndexFlatIP`)

During retrieval:

1. The user query is encoded into an embedding  
2. Similarity search is performed using FAISS  
3. The top-k most relevant chunks are returned  

In addition, a **field routing mechanism** is applied before dense retrieval.  
For structured queries (e.g., CPU, GPU, Wi-Fi), the system directly maps the query to the corresponding field, improving retrieval precision.

---

### Answer Generation

The system supports two answering strategies:

#### (1) Deterministic Answering (Default)

For structured specification queries, the answer is directly formatted from the retrieved chunk.

This approach:

- avoids hallucination  
- improves accuracy  
- reduces dependency on LLM generation  

---

#### (2) LLM-based Generation (llama.cpp)

For open-ended queries and system evaluation, the system uses a local LLM:

- Model: `Qwen2.5-1.5B-Instruct`
- Format: GGUF (quantized)
- Engine: `llama.cpp`

The retrieved chunks are injected into the prompt as context, and the model generates answers based on the provided information.

---

### Streaming Output

To support real-time response, the system enables streaming generation using `llama.cpp`.

```python
stream = llm(prompt, stream=True)
for chunk in stream:
    token = chunk["choices"][0]["text"]
    print(token, end="", flush=True)

---

## 4. System Evaluation

### Quantitative Evaluation

The system is evaluated using both deterministic answering and LLM-based generation.

#### Retrieval + Deterministic Answer

| Metric | Result |
|---|---:|
| Total Samples | 6 |
| Top-1 Retrieval Accuracy | 1.0000 |
| Top-3 Retrieval Accuracy | 1.0000 |
| Answer Accuracy | 1.0000 |

This shows that the retrieval pipeline correctly identifies the relevant field for all queries.

---

#### LLM Generation (llama.cpp)

| Metric | Result |
|---|---:|
| Average TTFT | 4455.23 ms |
| Average TPS | 4.19 tokens/s |
| Min TTFT | 1506.80 ms |
| Max TTFT | 9897.84 ms |

These metrics are measured using streaming generation.

---

### Qualitative Analysis

#### Retrieval Performance

The system achieves perfect retrieval accuracy due to the introduction of **field routing**.

For example:

- CPU queries are mapped to `中央處理器`
- Wi-Fi queries are mapped to `通訊`
- Side-specific queries are mapped to `連接埠-Right Side` or `連接埠-Left Side`

This demonstrates that field-aware retrieval is highly effective for structured specification data.

---

#### Generation Behavior

The LLM-based generation shows several limitations:

- Occasionally produces incorrect answers (e.g., Wi-Fi 7 support)
- May introduce hallucinated explanations not present in the source
- Generates unnecessary descriptive content for factual queries

---

#### Key Insight

> For structured specification QA, deterministic answering based on correctly retrieved fields is more reliable than free-form LLM generation.

---

#### Final Design Choice

Based on the evaluation:

- Deterministic answering is used as the default mode  
- LLM generation is retained only for:
  - streaming output  
  - latency evaluation (TTFT / TPS)  

This design ensures both **accuracy** and **system efficiency under 4GB VRAM constraint**.

## 5. How to Run

### Step 1: Install dependencies

This project uses `uv` for environment management.

```bash
uv sync
Step 2: Prepare data

Place the raw specification file in:

data/raw_spec.txt
Step 3: Run the system
uv run python src/main.py
Step 4: Run evaluation
uv run python eval/evaluate.py
