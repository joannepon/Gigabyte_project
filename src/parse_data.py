import json
import os
import re
from config import RAW_SPEC_PATH, PARSED_SPEC_PATH, CHUNKS_PATH

KEY_ALIAS = {
    "作業系統": "Operating System",
    "中央處理器": "CPU / Processor",
    "顯示晶片": "GPU / Graphics",
    "顯示器": "Display / Screen",
    "記憶體": "Memory / RAM",
    "儲存裝置": "Storage / SSD",
    "鍵盤種類": "Keyboard",
    "連接埠-Left Side": "Ports / Left Side I/O",
    "連接埠-Right Side": "Ports / Right Side I/O",
    "音效": "Audio",
    "通訊": "Connectivity / Wireless",
    "視訊鏡頭": "Camera / Webcam",
    "安全裝置": "Security",
    "電池": "Battery",
    "變壓器": "Adapter / Charger",
    "尺寸": "Dimensions",
    "重量": "Weight",
    "顏色": "Color",
}

def normalize_text(text: str) -> str:
    text = text.replace("。", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def parse_spec_text(raw_text: str):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    items = []
    current_key = None
    current_value_lines = []

    for line in lines:
        if re.match(r"^[^:：]+[:：]\s*$", line):
            if current_key is not None:
                items.append({
                    "key": current_key,
                    "value": normalize_text(" ".join(current_value_lines))
                })
            current_key = re.sub(r"[:：]\s*$", "", line).strip()
            current_value_lines = []
        else:
            current_value_lines.append(line)

    if current_key is not None:
        items.append({
            "key": current_key,
            "value": normalize_text(" ".join(current_value_lines))
        })

    return items

def clean_items(items):
    cleaned = []

    for item in items:
        key = item["key"].strip()
        value = item["value"].strip()

        if key == "連接埠" and value == "":
            continue

        if key in ["Left Side", "Right Side"]:
            cleaned.append({
                "key": f"連接埠-{key}",
                "value": value
            })
            continue

        if key == "變壓器" and "尺寸" in value:
            adapter_value, size_value = value.split("尺寸", 1)
            cleaned.append({
                "key": "變壓器",
                "value": adapter_value.strip()
            })
            cleaned.append({
                "key": "尺寸",
                "value": size_value.strip()
            })
            continue

        cleaned.append({
            "key": key,
            "value": value
        })

    return cleaned

def build_chunks(items):
    chunks = []
    for idx, item in enumerate(items):
        key = item["key"]
        value = item["value"]
        alias = KEY_ALIAS.get(key, "")
        text = f"欄位: {key}\nEnglish Field: {alias}\n內容: {value}"

        chunks.append({
            "id": idx,
            "key": key,
            "alias": alias,
            "value": value,
            "text": text
        })
    return chunks

def run_parsing_pipeline():
    with open(RAW_SPEC_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    parsed_items = parse_spec_text(raw_text)
    cleaned_items = clean_items(parsed_items)
    chunks = build_chunks(cleaned_items)

    os.makedirs("data", exist_ok=True)

    with open(PARSED_SPEC_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_items, f, ensure_ascii=False, indent=2)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print("Saved:")
    print(f"- {PARSED_SPEC_PATH}")
    print(f"- {CHUNKS_PATH}")

if __name__ == "__main__":
    run_parsing_pipeline()
