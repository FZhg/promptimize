import json
from typing import Dict, Any, Union, List
import subprocess
import hashlib
import json
import re

from pygments import highlight
from pygments.lexers import YamlLexer, JsonLexer
from pygments.formatters import TerminalFormatter
import yaml


def is_numeric(value):
    """that'd be nice if we had this in the std lib..."""
    return isinstance(value, (int, float, complex))


def is_iterable(obj):
    """that'd be nice if we had this in the std lib..."""
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def str_presenter(dumper, data):
    """
    Some hack to get yaml output to use look good for multiline,
    which is common in this package

    from: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
    """
    if len(data.splitlines()) > 1 or "\n" in data:
        text_list = [line.rstrip() for line in data.splitlines()]
        fixed_data = "\n".join(text_list)
        return dumper.represent_scalar("tag:yaml.org,2002:str", fixed_data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)


def extract_json(text: str, only_get_first_dict: bool = True):
    """
    Extract JSON objects from a given string and optionally return only the first object found.

    Args:
        text (str): The input string containing JSON objects.
        only_get_first_dict (bool, optional): Whether to return only the first JSON object found.
            Defaults to True.

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: The first JSON object found if
            `only_get_first_dict` is True, otherwise a list of JSON objects found in the input string.

    Example:

    >>> extract_json('Some text: {"key1": "value1", "key2": "value2"} and more text.')
    {'key1': 'value1', 'key2': 'value2'}

    >>> extract_json('{"a": 1, "b": 2} and {"c": 3, "d": 4}', only_get_first_dict=False)
    [{'a': 1, 'b': 2}, {'c': 3, 'd': 4}]
    """
    json_objects = extract_json_objects(text)  # type: ignore

    if only_get_first_dict:
        return json_objects[0] if json_objects else None
    else:
        return json_objects


def extract_json_objects(text: str, get_first: bool = True) -> List[Dict[str, Any]]:
    """
    Extract JSON objects from a given string by looking for matching curly brackets.

    Args:
        text (str): The input string containing JSON objects.

    Returns:
        List[Dict[str, Any]]: A list of JSON objects found in the input string.

    Example:

    >>> extract_json_objects('Some text: {"key1": "value1", "key2": "value2"} and more text.')
    [{'key1': 'value1', 'key2': 'value2'}]

    >>> extract_json_objects('No JSON objects in this text.')
    []

    >>> extract_json_objects('{"a": 1, "b": 2} and {"c": 3, "d": 4}')
    [{'a': 1, 'b': 2}, {'c': 3, 'd': 4}]
    """
    json_objects = []
    # man that regex is something... generated by GPT4...
    regex = r"(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\})"
    for match in re.finditer(regex, text):
        try:
            json_object = json.loads(match.group())
            json_objects.append(json_object)
        except json.JSONDecodeError:
            pass
    return json_objects


def short_hash(text, length=8):
    # Create a SHA-256 hash of the input string
    hash_object = hashlib.sha256(text.encode())

    # Convert the hash to a hexadecimal string
    hex_hash = hash_object.hexdigest()

    # Take a substring of the hex hash for a shorter version
    return hex_hash[:length]


def to_yaml(data, highlighted=True):
    data = yaml.dump(data, sort_keys=False)
    if highlighted:
        data = highlight(data, YamlLexer(), TerminalFormatter())
    return data


def to_json(data, highlighted=True):
    data = json.dumps(output, indent=2)
    highlighted = highlight(data, JsonLexer(), TerminalFormatter())


def serialize_object(data, style="yaml", highlighted=True):
    if style == "yaml":
        return to_yaml(data, highlighted)
    return to_json(data, highlighted)


def transform_strings(obj, transformation):
    """
    Recursively iterates through nested iterables (lists and tuples) and dictionaries,
    applying a given transformation function to all strings found.

    :param obj: The input object, which can be a string, dictionary, list, or tuple.
                Other types will be returned unchanged.
    :param transformation: A function that takes a single string argument and returns
                           a transformed string.
    :return: A new object with the same structure as the input object, but with all
             strings transformed by the given transformation function.
    """
    if isinstance(obj, str):
        return transformation(obj)
    elif isinstance(obj, dict):
        return {
            key: transform_strings(value, transformation) for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [transform_strings(item, transformation) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(transform_strings(item, transformation) for item in obj)
    else:
        return obj


def get_git_info():
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode("utf-8")
            .strip()
        )
        dirty = subprocess.call(["git", "diff-index", "--quiet", "HEAD"]) != 0

        return {"sha": sha, "branch": branch, "dirty": dirty}
    except subprocess.CalledProcessError:
        return None
