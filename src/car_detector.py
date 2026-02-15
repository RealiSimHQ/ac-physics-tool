"""
AC Car Detector
Identifies a car's make, model, and year from its data files.
Uses multiple signals: SCREEN_NAME, SHORT_NAME, folder name, and physics clues.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from .ini_parser import parse_ini_file, get_value, get_raw


# Known makes and common aliases
KNOWN_MAKES = {
    # Japanese
    'toyota': 'Toyota', 'lexus': 'Lexus', 'nissan': 'Nissan', 'infiniti': 'Infiniti',
    'honda': 'Honda', 'acura': 'Acura', 'mazda': 'Mazda', 'subaru': 'Subaru',
    'mitsubishi': 'Mitsubishi', 'suzuki': 'Suzuki', 'daihatsu': 'Daihatsu',
    # German
    'bmw': 'BMW', 'mercedes': 'Mercedes-Benz', 'mercedes-benz': 'Mercedes-Benz',
    'audi': 'Audi', 'porsche': 'Porsche', 'volkswagen': 'Volkswagen', 'vw': 'Volkswagen',
    'opel': 'Opel',
    # American
    'ford': 'Ford', 'chevrolet': 'Chevrolet', 'chevy': 'Chevrolet',
    'dodge': 'Dodge', 'chrysler': 'Chrysler', 'pontiac': 'Pontiac',
    'cadillac': 'Cadillac', 'buick': 'Buick', 'gmc': 'GMC',
    'corvette': 'Chevrolet',  # Corvette is Chevy
    'mustang': 'Ford',  # Mustang is Ford
    'camaro': 'Chevrolet',
    # Italian
    'ferrari': 'Ferrari', 'lamborghini': 'Lamborghini', 'alfa': 'Alfa Romeo',
    'alfa romeo': 'Alfa Romeo', 'fiat': 'Fiat', 'maserati': 'Maserati',
    'lancia': 'Lancia',
    # British
    'mclaren': 'McLaren', 'lotus': 'Lotus', 'aston martin': 'Aston Martin',
    'aston': 'Aston Martin', 'jaguar': 'Jaguar', 'bentley': 'Bentley',
    'rolls-royce': 'Rolls-Royce', 'mini': 'Mini', 'tvr': 'TVR',
    # Korean
    'hyundai': 'Hyundai', 'kia': 'Kia', 'genesis': 'Genesis',
    # Swedish
    'volvo': 'Volvo', 'koenigsegg': 'Koenigsegg',
}

# Common chassis/model codes → full identification
CHASSIS_CODES = {
    'e46': ('BMW', 'M3 (E46)', '1999-2006'),
    'e36': ('BMW', 'M3 (E36)', '1992-1999'),
    'e30': ('BMW', '3 Series (E30)', '1982-1994'),
    'e92': ('BMW', 'M3 (E92)', '2007-2013'),
    'f80': ('BMW', 'M3 (F80)', '2014-2018'),
    'f82': ('BMW', 'M4 (F82)', '2014-2020'),
    'g80': ('BMW', 'M3 (G80)', '2021+'),
    's13': ('Nissan', '240SX / Silvia (S13)', '1989-1994'),
    's14': ('Nissan', '240SX / Silvia (S14)', '1994-1998'),
    's15': ('Nissan', 'Silvia (S15)', '1999-2002'),
    '180sx': ('Nissan', '180SX (S13)', '1989-1998'),
    'ae86': ('Toyota', 'AE86 Corolla/Trueno', '1983-1987'),
    'jzx90': ('Toyota', 'Mark II / Chaser (JZX90)', '1992-1996'),
    'jzx100': ('Toyota', 'Mark II / Chaser (JZX100)', '1996-2001'),
    'jza80': ('Toyota', 'Supra (A80)', '1993-2002'),
    'a80': ('Toyota', 'Supra (A80)', '1993-2002'),
    'rx7': ('Mazda', 'RX-7', ''),
    'fd3s': ('Mazda', 'RX-7 (FD3S)', '1992-2002'),
    'fc3s': ('Mazda', 'RX-7 (FC3S)', '1985-1992'),
    'na': ('Mazda', 'MX-5 Miata (NA)', '1989-1997'),
    'nb': ('Mazda', 'MX-5 Miata (NB)', '1998-2005'),
    'nd': ('Mazda', 'MX-5 Miata (ND)', '2015+'),
    'gc8': ('Subaru', 'Impreza WRX (GC8)', '1992-2000'),
    'gdb': ('Subaru', 'Impreza WRX STI (GDB)', '2000-2007'),
    'c5': ('Chevrolet', 'Corvette (C5)', '1997-2004'),
    'c6': ('Chevrolet', 'Corvette (C6)', '2005-2013'),
    'c7': ('Chevrolet', 'Corvette (C7)', '2014-2019'),
    'c8': ('Chevrolet', 'Corvette (C8)', '2020+'),
    'ek9': ('Honda', 'Civic Type R (EK9)', '1997-2000'),
    'dc2': ('Honda', 'Integra Type R (DC2)', '1995-2001'),
    'dc5': ('Honda', 'Integra Type R (DC5)', '2001-2006'),
    'ap1': ('Honda', 'S2000 (AP1)', '1999-2003'),
    'ap2': ('Honda', 'S2000 (AP2)', '2004-2009'),
    'z33': ('Nissan', '350Z (Z33)', '2002-2009'),
    'z34': ('Nissan', '370Z (Z34)', '2009-2020'),
    'r32': ('Nissan', 'Skyline GT-R (R32)', '1989-1994'),
    'r33': ('Nissan', 'Skyline GT-R (R33)', '1995-1998'),
    'r34': ('Nissan', 'Skyline GT-R (R34)', '1999-2002'),
    'r35': ('Nissan', 'GT-R (R35)', '2007+'),
    'evo': ('Mitsubishi', 'Lancer Evolution', ''),
}


@dataclass
class CarIdentity:
    """Detected car identity."""
    make: str = "Unknown"
    model: str = "Unknown"
    year_range: str = ""
    chassis_code: str = ""
    confidence: float = 0.0
    source: str = ""  # What we detected from
    
    # Raw physics data
    total_mass: float = 0.0
    wheelbase: float = 0.0
    front_track: float = 0.0
    rear_track: float = 0.0
    drivetrain: str = ""
    steer_lock: float = 0.0
    max_fuel: float = 0.0
    
    # Suspension info
    front_susp_type: str = ""
    rear_susp_type: str = ""
    front_spring_rate: float = 0.0
    rear_spring_rate: float = 0.0
    
    # Files found
    files_found: list = field(default_factory=list)
    lut_files: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"{'='*50}"]
        lines.append(f"  {self.make} {self.model}")
        if self.year_range:
            lines.append(f"  Years: {self.year_range}")
        if self.chassis_code:
            lines.append(f"  Chassis: {self.chassis_code}")
        lines.append(f"  Confidence: {self.confidence:.0%} (from {self.source})")
        lines.append(f"{'='*50}")
        lines.append(f"  Mass: {self.total_mass:.1f} kg")
        lines.append(f"  Wheelbase: {self.wheelbase:.3f} m")
        lines.append(f"  Track F/R: {self.front_track:.3f} / {self.rear_track:.3f} m")
        lines.append(f"  Drivetrain: {self.drivetrain}")
        lines.append(f"  Steering Lock: {self.steer_lock:.0f}°")
        lines.append(f"  Fuel Capacity: {self.max_fuel:.0f} L")
        lines.append(f"  Suspension F: {self.front_susp_type} @ {self.front_spring_rate:.0f} N/m")
        lines.append(f"  Suspension R: {self.rear_susp_type} @ {self.rear_spring_rate:.0f} N/m")
        lines.append(f"  Data files: {len(self.files_found)}")
        lines.append(f"  LUT files: {len(self.lut_files)}")
        return '\n'.join(lines)


def detect_car(data_folder: str | Path) -> CarIdentity:
    """Detect car identity from an AC data folder."""
    data_folder = Path(data_folder)
    identity = CarIdentity()
    
    # Inventory all files
    if data_folder.is_dir():
        identity.files_found = [f.name for f in data_folder.iterdir() if f.is_file()]
        identity.lut_files = [f for f in identity.files_found if f.endswith('.lut')]
    
    # Parse car.ini
    car_ini = data_folder / 'car.ini'
    if car_ini.exists():
        car = parse_ini_file(car_ini)
        
        screen_name = get_raw(car, 'INFO', 'SCREEN_NAME', '')
        short_name = get_raw(car, 'INFO', 'SHORT_NAME', '')
        
        identity.total_mass = get_value(car, 'BASIC', 'TOTALMASS', 0.0)
        identity.steer_lock = get_value(car, 'CONTROLS', 'STEER_LOCK', 0.0)
        identity.max_fuel = get_value(car, 'FUEL', 'MAX_FUEL', 0.0)
        
        # Try to identify from screen name first
        _identify_from_name(identity, screen_name, 'SCREEN_NAME')
        if identity.confidence < 0.5 and short_name:
            _identify_from_name(identity, short_name, 'SHORT_NAME')
    
    # Parse suspensions.ini
    susp_ini = data_folder / 'suspensions.ini'
    if susp_ini.exists():
        susp = parse_ini_file(susp_ini)
        identity.wheelbase = get_value(susp, 'BASIC', 'WHEELBASE', 0.0)
        identity.front_track = get_value(susp, 'FRONT', 'TRACK', 0.0)
        identity.rear_track = get_value(susp, 'REAR', 'TRACK', 0.0)
        identity.front_susp_type = get_raw(susp, 'FRONT', 'TYPE', '')
        identity.rear_susp_type = get_raw(susp, 'REAR', 'TYPE', '')
        identity.front_spring_rate = get_value(susp, 'FRONT', 'SPRING_RATE', 0.0)
        identity.rear_spring_rate = get_value(susp, 'REAR', 'SPRING_RATE', 0.0)
    
    # Parse drivetrain.ini
    dt_ini = data_folder / 'drivetrain.ini'
    if dt_ini.exists():
        dt = parse_ini_file(dt_ini)
        identity.drivetrain = get_raw(dt, 'TRACTION', 'TYPE', '')
    
    # Fallback: try folder name
    if identity.confidence < 0.5:
        folder_name = data_folder.parent.name if data_folder.name == 'data' else data_folder.name
        _identify_from_name(identity, folder_name, 'folder name')
    
    return identity


def _identify_from_name(identity: CarIdentity, name: str, source: str):
    """Try to identify make/model from a name string."""
    if not name:
        return
    
    name_lower = name.lower().strip()
    
    # Check chassis codes first (most specific)
    for code, (make, model, years) in CHASSIS_CODES.items():
        if code in name_lower.replace('-', '').replace(' ', ''):
            identity.make = make
            identity.model = model
            identity.year_range = years
            identity.chassis_code = code.upper()
            identity.confidence = 0.9
            identity.source = f"{source}: '{name}'"
            return
    
    # Check known makes
    for alias, make in KNOWN_MAKES.items():
        if alias in name_lower:
            identity.make = make
            # Try to extract model (everything after the make name)
            idx = name_lower.find(alias)
            remainder = name[idx + len(alias):].strip().strip('-_').strip()
            if remainder:
                identity.model = remainder
            else:
                identity.model = name
            identity.confidence = 0.7
            identity.source = f"{source}: '{name}'"
            return
    
    # Last resort: use the full name as model
    identity.model = name
    identity.confidence = 0.3
    identity.source = f"{source}: '{name}' (unrecognized)"
