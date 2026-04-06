def format_answer_from_chunk(query: str, chunk: dict) -> str:
    q = query.lower()
    key = chunk["key"]
    value = chunk["value"]

    if key == "中央處理器":
        return f"答案：{value}\n欄位：{key}"

    if key == "顯示晶片":
        return f"答案：{value}\n欄位：{key}"

    if key == "通訊":
        if "wifi" in q or "wi-fi" in q or "無線" in q:
            if "WIFI 7" in value or "WiFi 7" in value or "802.11be" in value:
                return f"答案：Yes, it supports Wi-Fi 7.\n欄位：{key}"
        return f"答案：{value}\n欄位：{key}"

    if key == "電池":
        return f"答案：{value}\n欄位：{key}"

    if key in ["連接埠-Left Side", "連接埠-Right Side"]:
        if "thunderbolt 5" in q and ("Thunderbolt™5" in value or "Thunderbolt 5" in value):
            return f"答案：Yes, it has Thunderbolt 5.\n欄位：{key}"

        if "thunderbolt 4" in q and ("Thunderbolt™4" in value or "Thunderbolt 4" in value):
            return f"答案：Yes, it has Thunderbolt 4.\n欄位：{key}"

        return f"答案：{value}\n欄位：{key}"

    return f"答案：{value}\n欄位：{key}"
