"""
AC Data Folder Scanner
Handles multiple folder layouts:
1. Standard: car/data/car.ini, suspensions.ini, etc.
2. Prefixed: car/data/PREFIX_car.ini, PREFIX_suspensions.ini, etc.
3. Nested: car/data/data/ (subfolder with full data)
4. Ryan's format: files at top level with prefix, data/ subfolder with full set
"""

from pathlib import Path
from dataclasses import dataclass, field


# Core physics files we look for
CORE_FILES = {
    'car.ini',
    'suspensions.ini', 
    'tyres.ini',
    'drivetrain.ini',
    'engine.ini',
}

OPTIONAL_FILES = {
    'aero.ini',
    'brakes.ini',
    'bumpstops.ini',
    'dampers.ini',
    'electronics.ini',
    'setup.ini',
    'ai.ini',
    'driver3d.ini',
}


@dataclass
class ScanResult:
    """Result of scanning a folder for AC physics data."""
    root_path: Path = None
    data_path: Path = None  # Where the actual data files live
    layout: str = ""  # "standard", "prefixed", "nested", "flat"
    prefix: str = ""  # File prefix if any (e.g., "BMW_E46_")
    
    core_files: dict = field(default_factory=dict)   # logical name → actual path
    optional_files: dict = field(default_factory=dict)
    lut_files: list = field(default_factory=list)
    unknown_files: list = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        return 'car.ini' in self.core_files
    
    def summary(self) -> str:
        lines = [f"Scan: {self.root_path}"]
        lines.append(f"Layout: {self.layout}" + (f" (prefix: {self.prefix})" if self.prefix else ""))
        lines.append(f"Data path: {self.data_path}")
        lines.append(f"Core files: {len(self.core_files)}/{len(CORE_FILES)}")
        for name, path in self.core_files.items():
            lines.append(f"  ✓ {name} → {path.name}")
        missing = CORE_FILES - set(self.core_files.keys())
        for name in sorted(missing):
            lines.append(f"  ✗ {name}")
        lines.append(f"Optional files: {len(self.optional_files)}")
        for name in sorted(self.optional_files.keys()):
            lines.append(f"  + {name}")
        lines.append(f"LUT files: {len(self.lut_files)}")
        return '\n'.join(lines)


def scan_folder(path: str | Path) -> ScanResult:
    """Scan a folder and find AC physics data files."""
    path = Path(path)
    result = ScanResult(root_path=path)
    
    if not path.is_dir():
        return result
    
    # Strategy 1: Look for data/ subfolder
    data_dir = path / 'data'
    if data_dir.is_dir():
        # Check if data/data/ exists (double nesting)
        inner_data = data_dir / 'data'
        if inner_data.is_dir() and _has_physics_files(inner_data):
            # Use the inner data folder as primary, outer for prefixed overview files
            result.data_path = inner_data
            result.layout = "nested"
            _scan_directory(inner_data, result)
            # Also check outer level for prefixed files
            _scan_for_prefixed(data_dir, result)
            return result
        
        # Standard data/ folder
        if _has_physics_files(data_dir):
            result.data_path = data_dir
            result.layout = "standard"
            _scan_directory(data_dir, result)
            return result
        
        # Check for prefixed files in data/
        prefix = _detect_prefix(data_dir)
        if prefix:
            result.data_path = data_dir
            result.layout = "prefixed"
            result.prefix = prefix
            _scan_directory(data_dir, result, prefix)
            return result
    
    # Strategy 2: Files directly in the given folder
    if _has_physics_files(path):
        result.data_path = path
        result.layout = "flat"
        _scan_directory(path, result)
        return result
    
    # Strategy 3: Prefixed files in given folder
    prefix = _detect_prefix(path)
    if prefix:
        result.data_path = path
        result.layout = "prefixed"
        result.prefix = prefix
        _scan_directory(path, result, prefix)
        return result
    
    return result


def _has_physics_files(directory: Path) -> bool:
    """Check if directory has standard-named physics files."""
    files = {f.name.lower() for f in directory.iterdir() if f.is_file()}
    return 'car.ini' in files or 'suspensions.ini' in files


def _detect_prefix(directory: Path) -> str:
    """Detect a file prefix from physics files in a directory."""
    for f in directory.iterdir():
        if f.is_file() and f.name.lower().endswith('_car.ini'):
            return f.name[:-len('car.ini')]
    for f in directory.iterdir():
        if f.is_file() and f.name.lower().endswith('_suspensions.ini'):
            return f.name[:-len('suspensions.ini')]
    return ""


def _scan_directory(directory: Path, result: ScanResult, prefix: str = ""):
    """Scan a directory for physics files with optional prefix."""
    for f in directory.iterdir():
        if not f.is_file():
            continue
        
        name_lower = f.name.lower()
        
        # Strip prefix for matching
        if prefix:
            if name_lower.startswith(prefix.lower()):
                logical_name = f.name[len(prefix):]
            else:
                logical_name = f.name
        else:
            logical_name = f.name
        
        logical_lower = logical_name.lower()
        
        # Check core files
        if logical_lower in CORE_FILES:
            result.core_files[logical_lower] = f
        elif logical_lower in OPTIONAL_FILES:
            result.optional_files[logical_lower] = f
        elif f.suffix.lower() == '.lut':
            result.lut_files.append(f)
        elif f.suffix.lower() in ('.ini', '.lut'):
            result.unknown_files.append(f)


def _scan_for_prefixed(directory: Path, result: ScanResult):
    """Look for prefixed overview files (like BMW_E46_car.ini alongside data/)."""
    prefix = _detect_prefix(directory)
    if not prefix:
        return
    result.prefix = prefix
    for f in directory.iterdir():
        if not f.is_file():
            continue
        name_lower = f.name.lower()
        if name_lower.startswith(prefix.lower()):
            logical = f.name[len(prefix):].lower()
            if logical in CORE_FILES and logical not in result.core_files:
                result.core_files[logical] = f
