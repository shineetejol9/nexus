import csv
from datetime import datetime

from backend.rules import validate_business_rules


def detect_column_type(values):
    number_count = 0
    date_count = 0
    text_count = 0
    alphanumeric_count = 0

    for value in values:
        value = value.strip()

        if value == "":
            continue

        try:
            float(value)
            number_count += 1
            continue
        except:
            pass

        try:
            datetime.strptime(value, "%Y-%m-%d")
            date_count += 1
            continue
        except:
            pass

        if value.isalpha():
            text_count += 1
        elif value.isalnum():
            alphanumeric_count += 1
        else:
            text_count += 1

    counts = {
        "NUMBER": number_count,
        "DATE": date_count,
        "TEXT": text_count,
        "ALPHANUMERIC": alphanumeric_count
    }

    return max(counts, key=counts.get)


def is_valid(value, data_type):
    value = value.strip()

    if value == "":
        return False

    if data_type == "NUMBER":
        try:
            return float(value) > 0
        except:
            return False

    if data_type == "DATE":
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except:
            return False

    if data_type == "TEXT":
        return value.replace(" ", "").isalpha()

    if data_type == "ALPHANUMERIC":
        return value.isalnum()

    return False


def clean_file(file_path, rules=None):

    # Read CSV
    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        return [], []

    # Detect column types
    column_types = {}

    for column in rows[0]:

        values = [
            row[column]
            for row in rows
        ]

        column_types[column] = detect_column_type(values)

    clean_data = []
    bad_data = []

    seen_rows = set()

    # Validate each row
    for row in rows:

        row_tuple = tuple(row.values())

        # Check duplicate row
        if row_tuple in seen_rows:
            bad_data.append(row)
            continue

        seen_rows.add(row_tuple)

        # Generic validation
        valid = True

        for column, value in row.items():

            data_type = column_types[column]

            if not is_valid(value, data_type):
                valid = False
                break

        if not valid:
            bad_data.append(row)
            continue

        # Business-rule validation
        if rules is not None:

            if not validate_business_rules(row, rules):
                bad_data.append(row)
                continue

        # Row passed all validation
        clean_data.append(row)

    return clean_data, bad_data