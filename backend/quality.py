import csv
from datetime import datetime


def load_csv(file_path):

    with open(file_path, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        return list(reader)


def is_valid_value(value):

    value = value.strip()

    if value == "":
        return False

    # Number
    try:
        number = float(value)

        if number > 0:
            return True
        else:
            return False

    except:
        pass

    # Date
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True

    except:
        pass

    # Text
    if value.replace(" ", "").isalpha():
        return True

    # Alphanumeric
    if value.isalnum():
        return True

    return False


def detect_type(value):

    value = value.strip()

    if value == "":
        return "EMPTY"

    # Number
    try:
        float(value)
        return "NUMBER"

    except:
        pass

    # Date
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return "DATE"

    except:
        pass

    # Text
    if value.replace(" ", "").isalpha():
        return "TEXT"

    # Alphanumeric
    if value.isalnum():
        return "ALPHANUMERIC"

    return "OTHER"


def calculate_completeness(rows):

    if not rows:
        return 0

    total_values = 0
    filled_values = 0

    for row in rows:

        for value in row.values():

            total_values += 1

            if value is not None and value.strip() != "":
                filled_values += 1

    score = (filled_values / total_values) * 100

    return score


def calculate_validity(rows):

    if not rows:
        return 0

    valid_values = 0
    total_values = 0

    for row in rows:

        for value in row.values():

            total_values += 1

            if is_valid_value(value):
                valid_values += 1

    score = (valid_values / total_values) * 100

    return score


def calculate_uniqueness(rows):

    if not rows:
        return 0

    unique_rows = set()

    for row in rows:

        row_tuple = tuple(row.values())

        unique_rows.add(row_tuple)

    total_rows = len(rows)
    unique_count = len(unique_rows)

    score = (unique_count / total_rows) * 100

    return score


def calculate_consistency(rows):

    if not rows:
        return 0

    total_values = 0
    consistent_values = 0

    columns = rows[0].keys()

    for column in columns:

        expected_type = None

        # Find first non-empty value
        for row in rows:

            value = row[column]

            if value is not None and value.strip() != "":
                expected_type = detect_type(value)
                break

        if expected_type is None:
            continue

        # Check values against expected type
        for row in rows:

            value = row[column]

            if value is None or value.strip() == "":
                continue

            total_values += 1

            actual_type = detect_type(value)

            if actual_type == expected_type:
                consistent_values += 1

    if total_values == 0:
        return 0

    score = (consistent_values / total_values) * 100

    return score

def calculate_timeliness(rows):

    if not rows:
        return 0

    total_dates = 0
    valid_dates = 0

    for row in rows:

        for column, value in row.items():

            # Look for date columns
            if "date" in column.lower():

                total_dates += 1

                try:
                    datetime.strptime(
                        value.strip(),
                        "%Y-%m-%d"
                    )

                    valid_dates += 1

                except:
                    pass

    if total_dates == 0:
        return 100

    score = (valid_dates / total_dates) * 100

    return score


def calculate_quality_score(
    completeness,
    validity,
    uniqueness,
    consistency,
    timeliness
):

    score = (
        completeness
        + validity
        + uniqueness
        + consistency
        + timeliness
    ) / 5

    return score

# Test Quality Engine

if __name__ == "__main__":

    # Test Quality Engine

    file_path = "../data/raw/students.csv"

    rows = load_csv(file_path)

    completeness = calculate_completeness(rows)
    validity = calculate_validity(rows)
    uniqueness = calculate_uniqueness(rows)
    consistency = calculate_consistency(rows)
    timeliness = calculate_timeliness(rows)

    quality_score = calculate_quality_score(
        completeness,
        validity,
        uniqueness,
        consistency,
        timeliness
    )

    print("Completeness:", completeness)
    print("Validity:", validity)
    print("Uniqueness:", uniqueness)
    print("Consistency:", consistency)
    print("Quality Score:", quality_score)
    print("Timeliness:", timeliness)