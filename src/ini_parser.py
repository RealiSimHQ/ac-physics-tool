"""
AC Physics INI Parser
Reads and parses Assetto Corsa physics data files (car.ini, suspensions.ini, 
tyres.ini, drivetrain.ini, engine.ini) into structured Python dicts.

Handles AC-specific quirks:
- Inline comments with ; 
- Duplicate keys (some sections have repeated entries)
- LUT file references
- Numeric values with units in comments
"""

import re
from pathlib import Path
from collections import OrderedDict


def parse_ini_file(filepath: str | Path) -> dict:
    """Parse an AC physics INI file into a nested dict of sections."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = filepath.read_text(encoding='utf-8', errors='replace')
    return parse_ini_string(content)


def parse_ini_string(content: str) -> dict:
    """Parse AC INI content string into structured dict."""
    sections = OrderedDict()
    current_section = None
    
    for line in content.splitlines():
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Section header
        section_match = re.match(r'^\[(.+)\]$', line)
        if section_match:
            current_section = section_match.group(1)
            if current_section not in sections:
                sections[current_section] = OrderedDict()
            continue
        
        # Skip lines before any section
        if current_section is None:
            continue
        
        # Key=Value pair (with optional inline comment)
        kv_match = re.match(r'^([A-Za-z0-9_]+)\s*=\s*(.*?)(?:\s*;(.*))?$', line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()
            comment = kv_match.group(3).strip() if kv_match.group(3) else None
            
            # Try to parse numeric values
            parsed_value = _parse_value(value)
            
            entry = {
                'raw': value,
                'value': parsed_value,
            }
            if comment:
                entry['comment'] = comment
            
            # Handle duplicate keys (append _N)
            if key in sections[current_section]:
                n = 2
                while f"{key}_{n}" in sections[current_section]:
                    n += 1
                key = f"{key}_{n}"
            
            sections[current_section][key] = entry
        
        # Comment-only lines (starting with ;)
        # Skip these silently
    
    return sections


def _parse_value(value: str):
    """Try to parse a value as number, tuple of numbers, or leave as string."""
    if not value:
        return None
    
    # Check for comma-separated values (coordinates like "0.0, -0.395, -0.032")
    if ',' in value:
        parts = [p.strip() for p in value.split(',')]
        try:
            return tuple(float(p) for p in parts)
        except ValueError:
            return value
    
    # Try float
    try:
        f = float(value)
        # Return int if it's a whole number
        if f == int(f) and '.' not in value:
            return int(value)
        return f
    except ValueError:
        pass
    
    return value


def get_value(sections: dict, section: str, key: str, default=None):
    """Convenience: get a parsed value from sections dict."""
    if section in sections and key in sections[section]:
        return sections[section][key]['value']
    return default


def get_raw(sections: dict, section: str, key: str, default=None):
    """Convenience: get the raw string value."""
    if section in sections and key in sections[section]:
        return sections[section][key]['raw']
    return default


def list_lut_references(sections: dict) -> list[str]:
    """Find all LUT file references in parsed sections."""
    luts = []
    for section_name, section in sections.items():
        for key, entry in section.items():
            raw = entry.get('raw', '')
            if isinstance(raw, str) and raw.endswith('.lut'):
                luts.append(raw)
    return luts


def parse_lut_file(filepath: str | Path) -> list[tuple[float, float]]:
    """Parse an AC LUT (lookup table) file. Format: input|output per line."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"LUT not found: {filepath}")
    
    points = []
    for line in filepath.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        if '|' in line:
            parts = line.split('|')
            try:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                points.append((x, y))
            except (ValueError, IndexError):
                continue
    return points
