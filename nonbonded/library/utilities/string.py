import re


def camel_to_snake_case(camel_string: str):
    """Converts a string with Camel case formatting to one with snake case.

    E.g. "SomeName" -> "some_name"
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_string.replace(" ", "")).lower()


def camel_to_kebab_case(camel_string: str):
    """Converts a string with Camel case formatting to one with kebab case.

    E.g. "SomeName" -> "some-name"
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "-", camel_string.replace(" ", "")).lower()
