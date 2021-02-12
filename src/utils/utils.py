import re


def check_name(name, pattern):
    regex = re.compile(pattern)
    return regex.match(name) is not None





