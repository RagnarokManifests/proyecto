import json

file_path = r"C:\Users\juan\.gemini\antigravity-ide\brain\0ca49432-f26f-4d8a-87d7-aedf707bd03a\.system_generated\logs\transcript_full.jsonl"
output_path = "extracted_constancias.txt"

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get("type") == "TOOL_RESPONSE" and "view_file" in str(data):
                # Check if it was viewing constancias.html
                if "constancias.html" in str(data):
                    content = data.get("content", "")
                    with open(output_path, "a", encoding="utf-8") as out:
                        out.write(content + "\n=====================\n")
        except:
            pass

print("Extraction complete.")
