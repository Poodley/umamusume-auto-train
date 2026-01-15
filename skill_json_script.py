import json
import re
import pickle

OUTPUT_FILE = "skills.json"

def parse_skills(text: str):
    entries = []

    # Split on one or more blank lines
    blocks = [b for b in text.split("\n\n") if b.strip()]

    for block in blocks:
        lines = block.strip().splitlines()

        # Enforce the expected format
        if len(lines) < 2:
            continue  # skip malformed entries

        name = lines[0].strip()
        description = lines[1].strip()

        entries.append({
            "name": name,
            "description": description
        })

    return entries

def make_dict(data):
    skill_dict = {}

    # Split data into blocks separated by empty lines
    blocks = [b.strip() for b in data.strip().split("\n\n") if b.strip()]

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 2:
            continue  # skip malformed blocks

        skill_name = lines[0].strip()
        description = lines[1].strip()

        # Extract the last number in parentheses as skill_id
        match = re.findall(r"\((\d+)\)", description)
        if match:
            skill_id = int(match[-1])
            skill_dict[skill_id] = skill_name
        else:
            print(f"Warning: No skill ID found in description: {description}")
            print(skill_name)
            return
    return skill_dict


def main():
    with open("skills.txt", "r", encoding="utf-8") as f:
        text = f.read()
    data = make_dict(text)
    print(data)
    pickle.dump(data, open("skill_ids.pkl", "wb"))
    #with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    #    json.dump(data, f, ensure_ascii=False, indent=2)

    #print(f"Generated {len(data)} entries")
    #print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()