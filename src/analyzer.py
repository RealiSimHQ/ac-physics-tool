"""
AC Car Analyzer
The main entry point: takes any folder, figures out the layout,
identifies the car, and produces a full physics report.
"""

from pathlib import Path
from dataclasses import dataclass, field
from .folder_scanner import scan_folder, ScanResult
from .ini_parser import parse_ini_file, get_value, get_raw, list_lut_references, parse_lut_file
from .car_detector import detect_car, _identify_from_name, CarIdentity


@dataclass 
class PhysicsReport:
    """Complete physics analysis of an AC car."""
    identity: CarIdentity = None
    scan: ScanResult = None
    
    # From car.ini
    version: str = ""
    screen_name: str = ""
    short_name: str = ""
    total_mass: float = 0.0
    inertia: tuple = ()
    steer_lock: float = 0.0
    steer_ratio: float = 0.0
    linear_steer_rod_ratio: float = 0.0
    fuel_capacity: float = 0.0
    fuel_start: float = 0.0
    fuel_consumption: float = 0.0
    
    # From suspensions.ini
    wheelbase: float = 0.0
    cg_location: float = 0.0
    front_type: str = ""
    rear_type: str = ""
    front_track: float = 0.0
    rear_track: float = 0.0
    front_basey: float = 0.0
    rear_basey: float = 0.0
    front_spring_rate: float = 0.0
    rear_spring_rate: float = 0.0
    front_hub_mass: float = 0.0
    rear_hub_mass: float = 0.0
    arb_front: float = 0.0
    arb_rear: float = 0.0
    front_damp_bump: float = 0.0
    front_damp_rebound: float = 0.0
    rear_damp_bump: float = 0.0
    rear_damp_rebound: float = 0.0
    has_cosmic: bool = False
    has_dwb2: bool = False
    has_damper_luts: bool = False
    
    # From drivetrain.ini
    drivetrain_type: str = ""
    gear_count: int = 0
    gear_ratios: list = field(default_factory=list)
    final_drive: float = 0.0
    diff_power: float = 0.0
    diff_coast: float = 0.0
    diff_preload: float = 0.0
    
    # From engine.ini
    rpm_limiter: int = 0
    rpm_idle: int = 0
    engine_inertia: float = 0.0
    power_curve_file: str = ""
    has_turbo: bool = False
    turbo_max_boost: float = 0.0
    
    # Computed
    front_weight_pct: float = 0.0
    rear_weight_pct: float = 0.0
    cg_height_front: float = 0.0
    cg_height_rear: float = 0.0
    
    def summary(self) -> str:
        lines = []
        lines.append(f"╔{'═'*58}╗")
        lines.append(f"║  {self.screen_name or self.identity.model:^54}  ║")
        if self.identity.year_range:
            lines.append(f"║  {self.identity.year_range:^54}  ║")
        lines.append(f"╠{'═'*58}╣")
        
        lines.append(f"║  {'CHASSIS':^54}  ║")
        lines.append(f"║  Mass: {self.total_mass:.1f} kg (with driver, no fuel){'':>18}  ║")
        lines.append(f"║  Wheelbase: {self.wheelbase*1000:.0f} mm{'':>33}  ║")
        lines.append(f"║  Track F/R: {self.front_track*1000:.0f} / {self.rear_track*1000:.0f} mm{'':>26}  ║")
        if self.cg_location:
            self.front_weight_pct = self.cg_location * 100
            self.rear_weight_pct = (1 - self.cg_location) * 100
            lines.append(f"║  Weight dist: {self.front_weight_pct:.1f}% F / {self.rear_weight_pct:.1f}% R (sprung){'':>10}  ║")
        
        lines.append(f"║{'─'*58}║")
        lines.append(f"║  {'SUSPENSION':^54}  ║")
        lines.append(f"║  Front: {self.front_type}{'':>45}  ║"[:62] + "║")
        lines.append(f"║  Rear:  {self.rear_type}{'':>45}  ║"[:62] + "║")
        lines.append(f"║  Springs F/R: {self.front_spring_rate:.0f} / {self.rear_spring_rate:.0f} N/m{'':>18}  ║"[:62] + "║")
        lines.append(f"║  ARB F/R: {self.arb_front:.0f} / {self.arb_rear:.0f} N/m{'':>22}  ║"[:62] + "║")
        lines.append(f"║  Hub mass F/R: {self.front_hub_mass:.2f} / {self.rear_hub_mass:.2f} kg{'':>16}  ║"[:62] + "║")
        features = []
        if self.has_cosmic: features.append("COSMIC")
        if self.has_dwb2: features.append("DWB2")
        if self.has_damper_luts: features.append("Damper LUTs")
        if features:
            lines.append(f"║  CSP Features: {', '.join(features)}{'':>30}  ║"[:62] + "║")
        
        lines.append(f"║{'─'*58}║")
        lines.append(f"║  {'STEERING':^54}  ║")
        lines.append(f"║  Lock: {self.steer_lock:.0f}° ({self.steer_lock*2:.0f}° total){'':>28}  ║"[:62] + "║")
        lines.append(f"║  Ratio: {self.steer_ratio:.1f}:1{'':>38}  ║"[:62] + "║")
        
        if self.drivetrain_type:
            lines.append(f"║{'─'*58}║")
            lines.append(f"║  {'DRIVETRAIN':^54}  ║")
            lines.append(f"║  Type: {self.drivetrain_type}{'':>45}  ║"[:62] + "║")
            lines.append(f"║  Gears: {self.gear_count} speed, {self.final_drive:.3f} final{'':>22}  ║"[:62] + "║")
            if self.gear_ratios:
                ratios = ' / '.join(f"{g:.3f}" for g in self.gear_ratios)
                lines.append(f"║  Ratios: {ratios}{'':>30}  ║"[:62] + "║")
            lines.append(f"║  Diff: {self.diff_power*100:.0f}% pwr / {self.diff_coast*100:.0f}% coast / {self.diff_preload:.0f} Nm{'':>8}  ║"[:62] + "║")
        
        if self.rpm_limiter:
            lines.append(f"║{'─'*58}║")
            lines.append(f"║  {'ENGINE':^54}  ║")
            lines.append(f"║  RPM: {self.rpm_idle:.0f} - {self.rpm_limiter:.0f}{'':>32}  ║"[:62] + "║")
            if self.has_turbo:
                lines.append(f"║  Turbo: {self.turbo_max_boost:.2f} bar max{'':>32}  ║"[:62] + "║")
            else:
                lines.append(f"║  Naturally aspirated{'':>33}  ║"[:62] + "║")
        
        lines.append(f"║{'─'*58}║")
        lines.append(f"║  {'FILES':^54}  ║")
        lines.append(f"║  Core: {len(self.scan.core_files)} | Optional: {len(self.scan.optional_files)} | LUTs: {len(self.scan.lut_files)}{'':>12}  ║"[:62] + "║")
        
        lines.append(f"╚{'═'*58}╝")
        return '\n'.join(lines)


def analyze_car(path: str | Path) -> PhysicsReport:
    """Full analysis of an AC car from its folder."""
    path = Path(path)
    report = PhysicsReport()
    
    # Scan folder structure
    scan = scan_folder(path)
    report.scan = scan
    
    # If we found a nested data/ with the real files, also scan that
    data_subdir = path / 'data'
    if data_subdir.is_dir():
        inner_scan = scan_folder(data_subdir)
        # Merge: prefer inner scan's files for core physics
        for k, v in inner_scan.core_files.items():
            if k not in scan.core_files:
                scan.core_files[k] = v
        for k, v in inner_scan.optional_files.items():
            if k not in scan.optional_files:
                scan.optional_files[k] = v
        scan.lut_files.extend(inner_scan.lut_files)
    
    # Detect car identity
    identity = CarIdentity()
    
    # Parse car.ini
    if 'car.ini' in scan.core_files:
        car = parse_ini_file(scan.core_files['car.ini'])
        
        report.screen_name = get_raw(car, 'INFO', 'SCREEN_NAME', '')
        report.short_name = get_raw(car, 'INFO', 'SHORT_NAME', '')
        report.version = get_raw(car, 'HEADER', 'VERSION', '')
        report.total_mass = get_value(car, 'BASIC', 'TOTALMASS', 0.0)
        report.inertia = get_value(car, 'BASIC', 'INERTIA', ())
        report.steer_lock = get_value(car, 'CONTROLS', 'STEER_LOCK', 0.0)
        report.steer_ratio = get_value(car, 'CONTROLS', 'STEER_RATIO', 0.0)
        report.linear_steer_rod_ratio = get_value(car, 'CONTROLS', 'LINEAR_STEER_ROD_RATIO', 0.0)
        report.fuel_capacity = get_value(car, 'FUEL', 'MAX_FUEL', 0.0)
        report.fuel_start = get_value(car, 'FUEL', 'FUEL', 0.0)
        report.fuel_consumption = get_value(car, 'FUEL', 'CONSUMPTION', 0.0)
        
        # Identity from screen name
        if report.screen_name:
            _identify_from_name(identity, report.screen_name, 'SCREEN_NAME')
        if identity.confidence < 0.5 and report.short_name:
            _identify_from_name(identity, report.short_name, 'SHORT_NAME')
    
    # Fallback identity from folder name
    if identity.confidence < 0.5:
        folder_name = path.name
        _identify_from_name(identity, folder_name, 'folder name')
    
    # Parse suspensions.ini
    if 'suspensions.ini' in scan.core_files:
        susp = parse_ini_file(scan.core_files['suspensions.ini'])
        
        report.wheelbase = get_value(susp, 'BASIC', 'WHEELBASE', 0.0)
        report.cg_location = get_value(susp, 'BASIC', 'CG_LOCATION', 0.0)
        report.front_type = get_raw(susp, 'FRONT', 'TYPE', '')
        report.rear_type = get_raw(susp, 'REAR', 'TYPE', '')
        report.front_track = get_value(susp, 'FRONT', 'TRACK', 0.0)
        report.rear_track = get_value(susp, 'REAR', 'TRACK', 0.0)
        report.front_basey = get_value(susp, 'FRONT', 'BASEY', 0.0)
        report.rear_basey = get_value(susp, 'REAR', 'BASEY', 0.0)
        report.front_spring_rate = get_value(susp, 'FRONT', 'SPRING_RATE', 0.0)
        report.rear_spring_rate = get_value(susp, 'REAR', 'SPRING_RATE', 0.0)
        report.front_hub_mass = get_value(susp, 'FRONT', 'HUB_MASS', 0.0)
        report.rear_hub_mass = get_value(susp, 'REAR', 'HUB_MASS', 0.0)
        report.arb_front = get_value(susp, 'ARB', 'FRONT', 0.0)
        report.arb_rear = get_value(susp, 'ARB', 'REAR', 0.0)
        report.front_damp_bump = get_value(susp, 'FRONT', 'DAMP_BUMP', 0.0)
        report.front_damp_rebound = get_value(susp, 'FRONT', 'DAMP_REBOUND', 0.0)
        report.rear_damp_bump = get_value(susp, 'REAR', 'DAMP_BUMP', 0.0)
        report.rear_damp_rebound = get_value(susp, 'REAR', 'DAMP_REBOUND', 0.0)
        
        # CSP features
        report.has_cosmic = report.front_type == 'COSMIC' or report.rear_type == 'COSMIC'
        report.has_dwb2 = get_value(susp, '_EXTENSION', 'USE_DWB2', 0) == 1
        report.has_damper_luts = get_value(susp, '_EXTENSION', 'DAMPER_LUTS', 0) == 1
    
    # Parse drivetrain.ini
    if 'drivetrain.ini' in scan.core_files:
        dt = parse_ini_file(scan.core_files['drivetrain.ini'])
        
        report.drivetrain_type = get_raw(dt, 'TRACTION', 'TYPE', '')
        report.gear_count = get_value(dt, 'GEARS', 'COUNT', 0)
        report.final_drive = get_value(dt, 'GEARS', 'FINAL', 0.0)
        report.diff_power = get_value(dt, 'DIFFERENTIAL', 'POWER', 0.0)
        report.diff_coast = get_value(dt, 'DIFFERENTIAL', 'COAST', 0.0)
        report.diff_preload = get_value(dt, 'DIFFERENTIAL', 'PRELOAD', 0.0)
        
        report.gear_ratios = []
        for i in range(1, report.gear_count + 1):
            g = get_value(dt, 'GEARS', f'GEAR_{i}', None)
            if g is not None:
                report.gear_ratios.append(g)
    
    # Parse engine.ini
    if 'engine.ini' in scan.core_files:
        eng = parse_ini_file(scan.core_files['engine.ini'])
        
        report.rpm_limiter = get_value(eng, 'ENGINE_DATA', 'LIMITER', 0)
        report.rpm_idle = get_value(eng, 'ENGINE_DATA', 'MINIMUM', 0)
        report.engine_inertia = get_value(eng, 'ENGINE_DATA', 'INERTIA', 0.0)
        report.power_curve_file = get_raw(eng, 'HEADER', 'POWER_CURVE', '')
        
        # Check for turbo
        report.has_turbo = 'TURBO_0' in eng
        if report.has_turbo:
            report.turbo_max_boost = get_value(eng, 'TURBO_0', 'MAX_BOOST', 0.0)
    
    identity.total_mass = report.total_mass
    identity.wheelbase = report.wheelbase
    identity.front_track = report.front_track
    identity.rear_track = report.rear_track
    identity.drivetrain = report.drivetrain_type
    identity.steer_lock = report.steer_lock
    identity.max_fuel = report.fuel_capacity
    identity.files_found = list(scan.core_files.keys()) + list(scan.optional_files.keys())
    identity.lut_files = [f.name for f in scan.lut_files]
    
    report.identity = identity
    return report
