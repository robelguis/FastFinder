import sys
import pathlib
from collections import Counter

# Add app to path
sys.path.append(str(pathlib.Path(".").resolve()))
from app.engine.names import generate_golarion_name

ancestries = ["Human", "Dwarf", "Elf", "Goblin", "Halfling", "Orc", "Kobold", "Leshy", "Catfolk"]
generated_names = []

print("--- Generating 100 Character Names Across Ancestries ---")
for i in range(100):
    anc = ancestries[i % len(ancestries)]
    name = generate_golarion_name(anc)
    generated_names.append((anc, name))

# Audit results
name_counts = Counter([name for _, name in generated_names])
duplicates = {name: count for name, count in name_counts.items() if count > 1}

print(f"Total Unique Names: {len(name_counts)} / 100")
if duplicates:
    print(f"Duplicates found: {duplicates}")
else:
    print("Zero duplicates found in 100 samples!")

# Print first 10 samples
print("\nSample Output:")
for anc, name in generated_names[:10]:
    print(f"  [{anc}] {name}")
