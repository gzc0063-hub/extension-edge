import pandas as pd
import json
import os

def csv_to_json(csv_path, json_path):
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path}: not found")
        return

    df = pd.read_csv(csv_path, comment="#")

    # Strip whitespace from column names and string values
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Drop completely empty rows
    df.dropna(how='all', inplace=True)

    # Convert NaN to None for proper JSON serialization
    df = df.replace({pd.NA: None, float('nan'): None})

    records = df.to_dict(orient='records')

    with open(json_path, 'w') as f:
        json.dump(records, f, indent=2)

    print(f"Converted {csv_path} to {json_path}")

def main():
    os.makedirs('web/src/data', exist_ok=True)

    files_to_convert = [
        ('data/herbicides.csv', 'web/src/data/herbicides.json'),
        ('data/efficacy.csv', 'web/src/data/efficacy.json'),
        ('data/restrictions.csv', 'web/src/data/restrictions.json')
    ]

    for csv_in, json_out in files_to_convert:
        csv_to_json(csv_in, json_out)

if __name__ == "__main__":
    main()
