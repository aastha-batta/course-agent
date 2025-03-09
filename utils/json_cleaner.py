import json
import re

def clean_json_string(json_str):
    """
    Clean and fix common JSON formatting issues produced by LLMs
    """
    # Remove markdown code block markers if present
    json_str = re.sub(r'^```json', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'^```', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'```$', '', json_str, flags=re.MULTILINE)
    
    # Trim whitespace
    json_str = json_str.strip()
    
    # Try to parse as is first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Try some common fixes
    try:
        # Replace single quotes with double quotes (but not in content within already valid double quotes)
        in_string = False
        fixed_str = ""
        for i, char in enumerate(json_str):
            if char == '"' and (i == 0 or json_str[i-1] != '\\'):
                in_string = not in_string
            
            if char == "'" and not in_string:
                fixed_str += '"'
            else:
                fixed_str += char
                
        return json.loads(fixed_str)
    except json.JSONDecodeError:
        pass
    
    # Try more aggressive fixes
    try:
        # Sometimes LLMs add extra text before or after the JSON
        match = re.search(r'({[\s\S]*})', json_str)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass
    
    # If all attempts fail, raise an exception
    raise json.JSONDecodeError("Could not parse JSON after cleaning", json_str, 0)