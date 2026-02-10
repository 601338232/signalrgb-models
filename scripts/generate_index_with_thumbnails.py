import os
import json
from datetime import datetime

print("Starting index generation...")

# Check if models directory exists
if not os.path.exists("models"):
    print("ERROR: models directory does not exist")
    exit(1)

# List all JSON files
models = []
for filename in os.listdir("models"):
    if filename.endswith(".json") and filename != "index.json":
        models.append({
            "name": filename,
            "title": filename.replace(".json", ""),
            "leds": 0,
            "width": 0,
            "height": 0,
            "brand": "CompGen",
            "download": f"https://cdn.jsdelivr.net/gh/601338232/signalrgb-models/main/models/{filename}",
            "imageType": "none",
            "thumbnail": None
        })
        print(f"Added: {filename}")

# Create index
index_data = {
    "version": "2.0",
    "updated": datetime.now().isoformat(),
    "count": len(models),
    "models": models
}

# Save to file
with open("models/index.json", "w", encoding="utf-8") as f:
    json.dump(index_data, f, indent=2)

print(f"Done! Generated {len(models)} models")
