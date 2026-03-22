import csv
import json
from collections import defaultdict

# Paths
CSV_PATH = "API/app/data/Aviacion Terminos - Hoja 1.csv"
VOCAB_PATH = "API/app/data/vocabulary.json"
OUTPUT_PATH = "API/app/data/vocabulary.merged.json"

# Load existing vocabulary.json
def load_vocabulary():
    with open(VOCAB_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data

# Parse CSV and return dicts
def parse_csv():
    es_vocab = {}
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                en, es = row
                en, es = en.strip(), es.strip()
                if en and es:
                    es_vocab[en] = es
    return es_vocab

# Merge CSV terms into vocabulary.json
def merge_vocab(existing, csv_vocab):
    if "es" not in existing["vocabulary"]:
        existing["vocabulary"]["es"] = {}
    for k, v in csv_vocab.items():
        if k not in existing["vocabulary"]["es"]:
            existing["vocabulary"]["es"][k] = v
    return existing

if __name__ == "__main__":
    existing = load_vocabulary()
    csv_vocab = parse_csv()
    merged = merge_vocab(existing, csv_vocab)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Merged vocabulary written to {OUTPUT_PATH}")
