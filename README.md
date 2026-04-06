# Gigabyte_project
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

## 2. Key Idea

The source data is a **structured specification table**, not free-form text.

Instead of relying purely on LLM generation, this system:

1. Parses the specification into structured key-value fields  
2. Routes queries to the correct field (field-aware retrieval)  
3. Retrieves the exact specification chunk  
4. Uses **deterministic answer formatting**  

This design:

- Reduces hallucination  
- Improves accuracy  
- Works reliably under limited hardware constraints

- ## 3. Data Processing (Structured Specification Parsing)

### Overview

The raw product specification is provided as semi-structured text, where each field consists of a key (e.g., "中央處理器") followed by multiple lines of values.

The goal of this stage is to convert the raw text into **clean and structured key-value pairs**, which can later be used for retrieval and answering.

---

### Parsing Method

The parsing process is implemented using pure Python without external frameworks.

The main steps are:

1. **Line-by-line scanning**
   - The raw text is split into lines
   - Empty lines are removed

2. **Field detection**
   - A regular expression is used to detect field headers (e.g., lines ending with `:` or `：`)
   - Example:
     ```
     中央處理器:
     ```

3. **Multi-line value aggregation**
   - All lines following a field header are grouped as its value
   - This continues until the next field header is encountered

4. **Text normalization**
   - Remove unnecessary whitespace and line breaks
   - Standardize formatting into a single-line value

---

### Post-processing (Data Cleaning)

After parsing, additional cleaning steps are applied to improve structure and consistency:

- Merge nested fields:
  - `"Left Side"` → `"連接埠-Left Side"`
  - `"Right Side"` → `"連接埠-Right Side"`

- Split combined fields:
  - `"變壓器"` and `"尺寸"` are separated if they appear in the same block

- Remove empty or redundant fields:
  - For example, empty `"連接埠"` entries

---

### Output Format

The final output is stored as structured JSON:

```json
{
  "key": "中央處理器",
  "value": "Intel® Core™ Ultra 9 Processor 275HX ..."
}

---
