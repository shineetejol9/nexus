def detect_anomalies(rows):

    if not rows:
        return []

    anomalies = []

    for column in rows[0].keys():

        values = []

        for row in rows:
            try:
                value = float(row[column])
                values.append(value)
            except:
                pass

        if len(values) < 4:
            continue

        values.sort()

        q1_index = len(values) // 4
        q3_index = (3 * len(values)) // 4

        q1 = values[q1_index]
        q3 = values[q3_index]

        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for row in rows:

            try:
                value = float(row[column])
            except:
                continue

            if value < lower_bound or value > upper_bound:

                anomalies.append({
                    "column": column,
                    "value": value,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "row": row
                })

    return anomalies


if __name__ == "__main__":

    import csv

    with open(
        "data/processed/students_clean.csv",
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    result = detect_anomalies(rows)

    print(result)
    