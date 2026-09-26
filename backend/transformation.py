import csv
def clean_text(value):
    if value is None:
        return ""

    value = value.strip()
    value = " ".join(value.split())

    return value


def transform_row(row):
    transformed_row = {}

    for column, value in row.items():

        # Clean column name
        new_column = column.strip().lower().replace(" ", "_")

        # Clean value
        new_value = clean_text(value)

        transformed_row[new_column] = new_value

    return transformed_row


def transform_file(file_path):

    with open(file_path, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        transformed_data = []

        for row in reader:

            transformed_row = transform_row(row)

            transformed_data.append(transformed_row)

    return transformed_data


def save_transformed_data(data, output_path):

    if not data:
        return

    columns = data[0].keys()

    with open(output_path, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(file, fieldnames=columns)

        writer.writeheader()
        writer.writerows(data)