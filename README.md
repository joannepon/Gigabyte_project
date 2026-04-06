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

---
