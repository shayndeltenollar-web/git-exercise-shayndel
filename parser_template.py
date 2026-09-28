import json
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_xml(path: str | Path) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    data = {}
    
    def clean_key(tag):
        if '}' in tag:
            tag = tag.split('}')[-1]
        return tag.replace('-', '_')

    for elem in root.iter():
        tag = clean_key(elem.tag)
        if elem.text and elem.text.strip():
            data[tag] = elem.text.strip()
        for attr_name, attr_val in elem.attrib.items():
            data[clean_key(attr_name)] = attr_val
            
    if "test_option" not in data and "test-option" in data:
        data["test_option"] = data["test-option"]
    if "default_operation" not in data and "default-operation" in data:
        data["default_operation"] = data["default-operation"]
        
    return data

def parse_json(path: str | Path) -> dict:
    """Return site, device_count, enabled_devices, and roles from the JSON."""
    with open(path, 'r') as f:
        data = json.load(f)
        
    result = {}
    if isinstance(data, dict):
        for k, v in data.items():
            result[k] = v
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    result[sub_k] = sub_v
                    
    devices = data.get("devices", result.get("devices", []))
    if isinstance(devices, list):
        if "device_count" not in result:
            result["device_count"] = len(devices)
            
        if "enabled_devices" not in result:
            enabled = []
            for d in devices:
                if isinstance(d, dict):
                    is_enabled = d.get("enabled")
                    status = str(d.get("status", "")).lower()
                    # Catch boolean true, string "true", 1, or active/enabled status
                    if (is_enabled is True or is_enabled == 1 or str(is_enabled).lower() == "true" or
                        status in ["enabled", "active", "up"] or
                        (is_enabled is None and status == "")):
                        name = d.get("name") or d.get("id") or d.get("hostname")
                        if name:
                            enabled.append(name)
            result["enabled_devices"] = enabled
            
        if "roles" not in result:
            roles = set()
            for d in devices:
                if isinstance(d, dict):
                    role = d.get("role") or d.get("type")
                    if role:
                        roles.add(role)
            result["roles"] = sorted(list(roles))
            
    return result

def parse_yaml(path: str | Path) -> dict:
    """Return name, approved, duration_minutes, devices, and action from YAML."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        
    if not isinstance(data, dict):
        return {}
        
    result = {}
    for k, v in data.items():
        result[k] = v
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                result[sub_k] = sub_v
                
    return result

def build_summary(xml_path: str | Path, json_path: str | Path, yaml_path: str | Path) -> dict:
    """Combine the three parser results into one dictionary."""
    return {
        "xml": parse_xml(xml_path),
        "json": parse_json(json_path),
        "yaml": parse_yaml(yaml_path)
    }