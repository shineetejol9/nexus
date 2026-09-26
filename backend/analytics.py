def calculate_basic_statistics(rows):

    if not rows:
        return {}

    statistics = {}

    for column in rows[0].keys():

        values = []

        for row in rows:

            value = row[column]

            try:
                number = float(value)
                values.append(number)
            except:
                pass

        if values:

            statistics[column] = {
                "count": len(values),
                "minimum": min(values),
                "maximum": max(values),
                "average": sum(values) / len(values)
            }

    return statistics
def calculate_category_counts(rows):

    if not rows:
        return {}

    category_statistics = {}

    for column in rows[0].keys():

        counts = {}

        for row in rows:

            value = row[column].strip()

            if value == "":
                continue

            try:
                float(value)
                continue
            except:
                pass

            if value not in counts:
                counts[value] = 0

            counts[value] += 1

        if counts:
            category_statistics[column] = counts

    return category_statistics
def analyze_dataset(rows):

    if not rows:
        return {}

    numeric_statistics = calculate_basic_statistics(rows)

    category_statistics = calculate_category_counts(rows)

    return {
        "numeric": numeric_statistics,
        "categorical": category_statistics
    }
def calculate_kpis(rows):
    if not rows:
        return {}

    numeric_columns = 0
    categorical_columns = 0

    statistics = calculate_basic_statistics(rows)
    categories = calculate_category_counts(rows)

    numeric_columns = len(statistics)
    categorical_columns = len(categories)

    return {
        "total_rows": len(rows),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns
    }