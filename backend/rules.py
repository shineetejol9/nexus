import re
from datetime import datetime


def check_required(value):
    return value is not None and value.strip() != ""


def check_range(value, minimum=None, maximum=None):

    try:
        number = float(value)
    except:
        return False

    if minimum is not None and number < minimum:
        return False

    if maximum is not None and number > maximum:
        return False

    return True


def check_min(value, minimum):

    try:
        return float(value) >= minimum
    except:
        return False


def check_max(value, maximum):

    try:
        return float(value) <= maximum
    except:
        return False


def check_positive(value):

    try:
        return float(value) > 0
    except:
        return False


def check_non_negative(value):

    try:
        return float(value) >= 0
    except:
        return False


def check_integer(value):

    try:
        int(value)
        return True
    except:
        return False


def check_decimal(value):

    try:
        float(value)
        return True
    except:
        return False


def check_allowed_values(value, allowed_values):

    return value in allowed_values


def check_min_length(value, minimum):

    return len(value) >= minimum


def check_max_length(value, maximum):

    return len(value) <= maximum


def check_regex(value, pattern):

    return re.fullmatch(pattern, value) is not None


def check_date_format(value, date_format):

    try:
        datetime.strptime(value, date_format)
        return True
    except:
        return False


def check_email(value):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.fullmatch(pattern, value) is not None

def validate_business_rules(row, rules):

    for column, column_rules in rules.items():

        if column not in row:
            continue

        value = row[column]

        for rule_name, rule_value in column_rules.items():

            if rule_name == "required":

                if rule_value and not check_required(value):
                    return False

            elif rule_name == "range":

                if not check_range(
                    value,
                    rule_value.get("min"),
                    rule_value.get("max")
                ):
                    return False

            elif rule_name == "min":

                if not check_min(value, rule_value):
                    return False

            elif rule_name == "max":

                if not check_max(value, rule_value):
                    return False

            elif rule_name == "positive":

                if rule_value and not check_positive(value):
                    return False

            elif rule_name == "non_negative":

                if rule_value and not check_non_negative(value):
                    return False

            elif rule_name == "integer":

                if rule_value and not check_integer(value):
                    return False

            elif rule_name == "decimal":

                if rule_value and not check_decimal(value):
                    return False

            elif rule_name == "allowed_values":

                if not check_allowed_values(
                    value,
                    rule_value
                ):
                    return False

            elif rule_name == "min_length":

                if not check_min_length(
                    value,
                    rule_value
                ):
                    return False

            elif rule_name == "max_length":

                if not check_max_length(
                    value,
                    rule_value
                ):
                    return False

            elif rule_name == "regex":

                if not check_regex(
                    value,
                    rule_value
                ):
                    return False

            elif rule_name == "date_format":

                if not check_date_format(
                    value,
                    rule_value
                ):
                    return False

            elif rule_name == "email":

                if rule_value and not check_email(value):
                    return False

    return True