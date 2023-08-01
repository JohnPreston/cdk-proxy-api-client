"""Common tools and functions reused in secrets management functions"""

import re
from copy import deepcopy


def replace_string_in_dict_values(
    input_dict: dict, src_value: str, new_value: str, copy: bool = False
) -> dict:
    """
    Function to update all values in an input dictionary that will match with the new value.
    It uses the new value to set as regex and replaces it in the dict values for each key,
    allowing for any secret value and dynamic dict content.
    """

    src_re = re.compile(re.escape(src_value))
    if copy:
        updated_dict = deepcopy(input_dict)
    else:
        updated_dict = input_dict
    for key, value in updated_dict.items():
        if isinstance(value, str) and src_re.findall(value):
            updated_dict[key] = src_re.sub(new_value, value)
        elif not isinstance(value, str):
            print(f"The value for {key} is not a string. Skipping")
    if copy:
        return updated_dict
