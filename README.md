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

## 2. System Design

The system follows a structured RAG pipeline:
