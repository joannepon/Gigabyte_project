import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import CHUNKS_PATH, EMBED_MODEL_NAME

def detect_field(query: str):
    q = query.lower()

    if "cpu" in q or "processor" in q or "處理器" in q:
        return "中央處理器"
    if "gpu" in q or "graphics" in q or "rtx" in q or "顯卡" in q or "顯示晶片" in q:
        return "顯示晶片"
    if "display" in q or "screen" in q or "panel" in q or "螢幕" in q or "顯示器" in q:
        return "顯示器"
    if "wifi" in q or "wi-fi" in q or "bluetooth" in q or "wireless" in q or "通訊" in q or "無線" in q:
        return "通訊"
    if "battery" in q or "wh" in q or "電池" in q:
        return "電池"
    if "memory" in q or "ram" in q or "記憶體" in q:
        return "記憶體"
    if "storage" in q or "ssd" in q or "儲存" in q or "硬碟" in q:
        return "儲存裝置"
    if "adapter" in q or "charger" in q or "變壓器" in q or "充電器" in q:
        return "變壓器"
    if "dimension" in q or "size" in q or "尺寸" in q:
        return "尺寸"
    if "weight" in q or "重量" in q:
        return "重量"
    if "camera" in q or "webcam" in q or "鏡頭" in q:
        return "視訊鏡頭"
    if "security" in q or "tpm" in q or "安全" in q:
        return "安全裝置"
    if "audio" in q or "speaker" in q or "sound" in q or "音效" in q:
        return "音效"
    if "color" in q or "colour" in q or "顏色" in q:
        return "顏色"
    if "right" in q or "右側" in q or "右边" in q or "右邊" in q:
        return "連接埠-Right Side"
    if "left" in q or "左側" in q or "左边" in q or "左邊" in q:
        return "連接埠-Left Side"
    if "thunderbolt 5" in q:
        return "連接埠-Left Side"
    if "thunderbolt 4" in q:
        return "連接埠-Right Side"
    return None

class GigabyteRetriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        self.texts = [c["text"] for c in self.chunks]

        embeddings = self.embed_model.encode(
            self.texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        self.embeddings = np.array(embeddings, dtype="float32")

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(self.embeddings)

    def retrieve_dense(self, query, top_k=1):
        query_vec = self.embed_model.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype="float32")

        scores, indices = self.index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            results.append({
                "score": float(score),
                "chunk": self.chunks[idx]
            })
        return results

    def retrieve(self, query, top_k=1):
        target_field = detect_field(query)

        if target_field:
            for chunk in self.chunks:
                if chunk["key"] == target_field:
                    return [{"score": 999.0, "chunk": chunk}]

        return self.retrieve_dense(query, top_k=top_k)

def load_chunks():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
