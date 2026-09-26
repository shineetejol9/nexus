import csv
from datetime import datetime
def profile_csv(file_path):

    rows = load_csv(file_path)

    dataset_profile = profile_dataset(rows)

    column_profile = profile_columns(rows)

    return {
        "dataset": dataset_profile,
        "columns": column_profile
    }

def load_csv(file_path):

    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

    return rows


def detect_type(value):

    value = value.strip()

    if value == "":
        return "EMPTY"

    try:
        float(value)
        return "NUMBER"
    except:
        pass

    try:
        datetime.strptime(
            value,
            "%Y-%m-%d"
        )
        return "DATE"
    except:
        pass

    if value.replace(" ", "").isalpha():
        return "TEXT"

    if value.isalnum():
        return "ALPHANUMERIC"

    return "OTHER"


def count_missing(values):

    count = 0

    for value in values:

        if value is None or value.strip() == "":
            count += 1

    return count

def count_unique(values):

    unique_values = set()

    for value in values:

        if value is not None:
            unique_values.add(value.strip())

    return len(unique_values)

def count_duplicate_rows(rows):

    seen_rows = set()
    duplicate_count = 0

    for row in rows:

        row_tuple = tuple(row.values())

        if row_tuple in seen_rows:
            duplicate_count += 1
        else:
            seen_rows.add(row_tuple)

    return duplicate_count

def profile_columns(rows):

    profile = {}

    if not rows:
        return profile

    for column in rows[0].keys():

        values = []

        for row in rows:
            values.append(row[column])

        type_counts = {}

        for value in values:

            data_type = detect_type(value)

            if data_type not in type_counts:
                type_counts[data_type] = 0

            type_counts[data_type] += 1

        detected_type = max(
            type_counts,
            key=type_counts.get
        )

        profile[column] = {
            "type": detected_type,
            "type_counts": type_counts,
            "missing": count_missing(values),
            "unique": count_unique(values)
        }

    return profile
def profile_dataset(rows):

    if not rows:
        return {
            "rows": 0,
            "columns": 0,
            "duplicate_rows": 0
        }

    return {
        "rows": len(rows),
        "columns": len(rows[0]),
        "duplicate_rows": count_duplicate_rows(rows)
    }