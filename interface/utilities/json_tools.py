# © 2025 Numantic Solutions LLC
# MIT License
#
# Tools for working with json

import json

def create_json_lines_file(data: str,
                           filename: str):
    """
    Creates a JSON Lines file from a list of Python objects.

    Args:
        data: A list of Python objects to be written to the file.
        filename: The name of the file to be created.
    """
    with open(filename, 'w') as outfile:
        for item in data:
            json_string = json.dumps(item)
            outfile.write(json_string + '\n')


def read_jsonl_file_json(file_path):
    """Reads a JSONL file using the JSON library and yields each JSON object."""
    with open(file_path, 'r') as f:
        for line in f:
            try:
                obj = json.loads(line)
                yield obj
            except json.JSONDecodeError:
                pass
                # print(f"Skipping invalid JSON line: {line.strip()}")


def extract_json(text: str) -> dict:
    '''
    Function to remove unnecessary characters in a string containing an
    embedded JSON component
    '''

    pats = ["```json", "```", "\n"]
    for pat in pats:
        text = text.replace(pat, "")

    return json.loads(text)


def reduce_json(json_list: list,
                value_fld: str) -> list:

    '''
    Function to reduce a JSON string to only those JSON entries with data in the
    value_fld.  For example, in this JSON string item "3" has a value in the value
    field (value) while "8" and "9" do not. This function will remove those items
    from the JSON string and return a new JSON string which is shorter.
            "3":{"name":"Which category best describes you?",
                 "value":"Educator (school, district or ROE affiliated)",
                 "value_raw":"Educator (school, district or ROE affiliated)",
                 "id":3,"type":"radio",
                 "visible":true},
            "8":{"name":"Do you live in Illinois?",
                 "value":"",
                 "value_raw":"",
                 "id":8,"type": "select",
                 "visible":false},
             "9":{"name":"Which county do you live in?",
                  "value":"",
                  "value_raw":"",
                  "id":9,
                  "type":"select",
                  "visible":false}

    Args:
        json_list: A list of JSON strings to be cleaned.
        value_fld: A string which field to look to determine if the entry should stay

    Returns:
        list of JSON strings

    '''

    cleaned_json_list = []
    for jstr in json_list:

        meta_dict = json.loads(jstr)

        if type(meta_dict) != dict:

            new_meta_dict = {}

        else:

            value_keys = []
            for key in meta_dict.keys():

                # Only add keys with values
                if len(meta_dict[key][value_fld]) > 0:
                    value_keys.append(key)

            # Create a dictionary of only keys with values
            new_meta_dict = {}
            for key in value_keys:
                new_meta_dict[key] = meta_dict[key]

        # Create a json from the new dictionary and replace column value
        cleaned_json_list.append(json.dumps(new_meta_dict))

    return cleaned_json_list


def flatten_json(nested_json):
    """
    Recursively flattens a nested JSON object into a single-level dictionary.
    Keys are concatenated using a dot notation.
    """
    out = {}

    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], name + a + '.')
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else:
            out[name[:-1]] = x # Remove trailing dot from the key

    flatten(nested_json)
    return out


