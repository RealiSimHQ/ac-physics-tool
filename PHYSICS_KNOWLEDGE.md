# AC Physics Knowledge Base
## Comprehensive Research Document for the Physics Modification Tool

*Generated from: Arch's Physics Pipeline doc, Ryan's 4 completed cars, and reference files*

---

## Table of Contents
1. [Arch's Pipeline — Complete Notes](#1-archs-pipeline--complete-notes)
2. [Ryan's 4 Cars — Detailed Analysis](#2-ryans-4-cars--detailed-analysis)
3. [Cross-Reference Findings](#3-cross-reference-findings)
4. [Formulas for the Tool](#4-formulas-for-the-tool)
5. [What the Tool Gets WRONG](#5-what-the-tool-gets-wrong)
6. [Do NOT Auto-Calculate (Needs Geometry)](#6-do-not-auto-calculate)
7. [CAN Safely Auto-Calculate](#7-can-safely-auto-calculate)
8. [How Steering Modifications Actually Work](#8-how-steering-modifications-actually-work)

---

## 1. Arch's Pipeline — Complete Notes

### 1.1 car.ini

#### VERSION
- Must be `extended-2` for CSP extended physics features (Cphys)
- `1` or `2` for vanilla; `extended-1` or `extended-2` for Cphys

#### TOTALMASS
- **Sprung + unsprung + driver mass, but NOT fuel**
- Other fluids (coolant, oil) SHOULD be included
- Driver is typically 75kg
- Formula: `dry_weight + 75` (driver)

#### INERTIA
- This is the **SPRUNG** inertia, NOT total car inertia
- Input as dimension box (width, height, depth) in meters
- Unsprung mass generates its own inertia separately
- Typical values are SMALLER than the physical car dimensions
- Ryan's AE86: total `1.450, 1.200, 4.000` → sprung `1.182, 1.275, 3.902`
- Ryan's E46: `1.55575, 0.927798, 4.20573` (sprung)
- Ryan's 180SX: total `1.500, 1.170, 4.230` → sprung `1.220, 1.240, 4.220`
- Ryan's C6: total `1.691, 0.882, 3.822` → sprung `1.464, 0.920, 3.682`

#### GRAPHICS_OFFSET
- Moves the VISUAL body relative to wheels, referenced from CG
- Must be adjusted every time CG changes
- Input in meters: width, height, depth

#### STEER_LOCK
- In-cockpit steering wheel rotation, center to one side
- Input the REAL WORLD value; total range / 2
- Does NOT need to match user's wheel hardware
- Ryan's values: AE86=570°, E46=540°, 180SX=558°, C6=500°

#### STEER_RATIO
- Effective steering ratio used in solving road wheel angle
- Enter the real-world rack's value
- Ryan's values: AE86=13.80, E46=15.4, 180SX=14.30, C6=17.1

#### LINEAR_STEER_ROD_RATIO
- **Critical formula**: meters of rack travel per degree of steering wheel × STEER_RATIO
- Reverse the SIGN if car steers wrong direction (depends on rack position: front or behind wheel center)
- Positive = rack behind axle, Negative = rack in front of axle
- AE86: `-0.001674` (rack in front), derived: `-0.001977 / 16.30 * 13.80 = -0.001674`
- E46: `0.002155` (rack behind)
- 180SX: `-0.001281` (rack in front)
- C6: `0.001967`, derived: `(0.115 / (500*2)) * 17.1 = 0.001967`

**The C6 comment is KEY — it reveals the actual formula:**
```
LINEAR_STEER_ROD_RATIO = (total_rack_travel / (STEER_LOCK * 2)) * STEER_RATIO
```
Where total_rack_travel is in meters (e.g., 0.115m = 115mm)

#### RACK_TRAVEL_LUT
- Optional LUT file that maps steering wheel degrees → rack travel in meters
- Used when non-linear steering is desired
- AE86, 180SX, and C6 use this; E46 does NOT (uses DWB2 with LINEAR_STEER_ROD_RATIO only)

#### FFMULT
- Car-specific FFB gain multiplier
- Steering forces generated from rack-end positions
- Typical: 1.4-2.5

#### ASSIST_TORQUE_MAX / ASSIST_MAP_0
- Power steering simulation
- ASSIST_TORQUE_MAX: max assist torque in Nm
- ASSIST_MAP_0: LUT for speed-sensitive power steering

### 1.2 suspensions.ini

#### VERSION
- Use `4` for standard, `5` for COSMIC suspension features
- Ryan uses VERSION=4 for AE86 (COSMIC via _EXTENSION), VERSION=5 for 180SX/C6 (flex bodies)

#### _EXTENSION Section
- `TORQUE_MODE_EX=2`: Corrected force calculation for DWB/ML/STRUT — **always use 2**
- `FIX_PROGRESSIVE_RATE=1`: Fix for progressive springs — **always use 1**
- `USE_DWB2=1`: Comprehensive DWB features. E46 uses 1, others use 0
- `DAMPER_LUTS=1`: LUT-based dampers. AE86/C6/180SX use 1, E46 uses 0

#### _EXTENSION_FLEX Section (VERSION=5 only)
- Used by 180SX and C6 for subframe/chassis flex simulation
- `CFM_P`, `CFM_R`: Constraint Force Mixing (ODE parameters)
- `ERP_P`, `ERP_R`: Error Reduction Parameters
- `COMPACT_ARRANGEMENT=1`, `USE_FORCES=1`

#### WHEELBASE
- Longitudinal distance between front and rear axle, in meters
- AE86=2.400, E46=2.731, 180SX=2.475, C6=2.685

#### CG_LOCATION
- Distribution of **SPRUNG MASS** over wheels (NOT total car CG)
- 0.50 = 50% front
- AE86=0.600 (60% front sprung), E46=0.5112, 180SX=0.555, C6=0.530

#### BASEY (per axle)
- Controls sprung CG height
- A **negative** BASEY produces a **positive** CGH
- Formula: `CGH = tire_loaded_radius - |BASEY|`
- Or equivalently: `BASEY = -(CGH - tire_loaded_radius)` but this needs care with signs
- Actually: `BASEY = RADIUS - CGH` where negative means CG is above ground
- AE86: F/R = -0.250, E46: F/R = -0.210, 180SX: F/R = -0.250, C6: F/R = -0.170

#### TRACK
- Lateral distance between left/right tire contact patches at 0° camber at design height
- Input in meters

#### ROD_LENGTH (standard suspensions)
- Controls suspension height
- When ROD_LENGTH = SUSTRVL, suspension loads at design height

#### HUB_MASS
- Unsprung mass per wheel (per side for AXLE)
- **STRUT quirk**: Converts 20% to sprung mass → enter `intended / 0.80`
- COSMIC does NOT have this quirk
- Ryan's detailed breakdowns show exact component-level calculations
- AE86 Front: 33.9kg (includes wheel, tire, brake, knuckle, etc.)
- E46 Front: 46.98kg (extremely detailed: 35.236 + 8.177 + 3.563)
- C6 Front: 53.0kg, C6 Rear: 58.0kg

#### RIM_OFFSET
- Wheel offset adjustment, adds to X coordinates of suspension
- Formula to compensate track: `RIM_OFFSET = (new_track - current_track) / -2`
- E46: -0.0185 (M3 ET47 wheels on 325i geometry basis)

#### ARB (Anti-Roll Bar)
- Without EXTEND: `FRONT` and `REAR` are **WHEELRATES** in N/m
- With `EXTEND=1`: `FRONT` and `REAR` are **SPRINGRATES** and use motion ratio
- `FRONT_MOTION_RATIO=1.0` means wheelrate = springrate (MR already baked in)
- All of Ryan's COSMIC cars use EXTEND=1 with MR=1.0, meaning the values are effectively wheelrates

#### Spring Rate (SPRING_RATE or RATE in coilovers)
- Without COSMIC: `SPRING_RATE` is the **WHEELRATE**
- **STRUT quirk**: Applies pseudo-motion ratio ≈ `actual_MR * SPRING_RATE`
- With COSMIC coilovers: `RATE` is the actual spring rate, and `INSTALL_RATE` provides the installation stiffness
- `INSTALL_RATE` very high (16,670,000 or 1,000,000) = rigid mount (no bushing compliance)

#### Dampers
- `DAMP_BUMP` / `DAMP_REBOUND`: Slow speed damping rates in N/m/s (WHEELRATE)
- `DAMP_FAST_BUMP` / `DAMP_FAST_REBOUND`: High speed rates
- `DAMP_FAST_BUMPTHRESHOLD` / `DAMP_FAST_REBOUNDTHRESHOLD`: Knee speed in m/s
- With `DAMPER_LUTS=1`: Can use LUT files for detailed damper curves

#### Bumpstops and Packers
- `BUMPSTOP_GAP` (COSMIC) or `PACKER_RANGE` (standard): Gap before contact
- Standard: `PACKER_RANGE = SUSTRVL + intended_gap`
- COSMIC: `BUMPSTOP_GAP` is direct gap from coilover preload position
- `BUMP_STOP_RATE`: Wheelrate of packer/bumpstop
- STRUT/AXLE have hardcoded ~500,000 N/m for BUMPSTOP entries

#### Suspension Types
- **DWB** (Double Wishbone): Upper + lower arms with ball joints
- **STRUT** (MacPherson): Strut top/bottom + lower control arm + steering
- **ML** (Multi-Link): 5 joints (JOINT0-4) each with CAR and TYRE points
- **AXLE**: Solid axle, references from axle center, 4-5 links
- **COSMIC** (CSP): Fully custom kinematic suspension using bodies, joints, sliders, hinges

#### COSMIC Suspension Details
All 4 of Ryan's cars use COSMIC. Key concepts:
- `BODY_N_NAME`: Named rigid bodies (strut bodies, axle bodies, subframes, LCA bodies)
- `DJ_N`: Distance joints (constrain distance between two points)
- `J_N`: Ball joints (fixed point shared between bodies)
- `SLIDER_N`: Slider joints (linear motion along an axis)
- `HJ_N`: Hinge joints (rotation around an axis)
- `STEER_JOINT_0`: The tie rod connection for steering
- `_LENGTH_OFFSET`: Adjusts effective link length (used for camber/caster/toe adjustment)
- `_KP=0` or `_KP=1`: Determines if the joint constrains rotation (0=free, 1=locked)
- `_PARITY`: Controls mirroring behavior

#### Suspension Coordinate System
- Referenced from wheel center of one corner
- **X positive** = towards car center (inboard)
- **X negative** = away from car center (outboard)
- **Y positive** = above wheel center
- **Y negative** = below wheel center
- **Z positive** = in front of wheel center
- **Z negative** = behind wheel center
- AXLE references from axle center instead

### 1.3 tyres.ini

#### VERSION
- Use `10` for current tire model (AE86, 180SX drift tires)
- Use `11` for extended features (C6, E46 performance tires)

#### Key Tire Parameters

| Parameter | Description | Units |
|-----------|-------------|-------|
| WIDTH | Skid decal width (visual only) | meters |
| RADIUS | Unloaded tire radius at nominal inflation | meters |
| RIM_RADIUS | Collision radius for wheel | meters |
| ANGULAR_INERTIA | Rotational inertia of tire+wheel+brake | kg*m² |
| RATE | Vertical spring rate at PRESSURE_STATIC | N/m |
| DAMP | Tire damping at nominal load | N/m/s |
| FZ0 | Reference load for tire behavior | Newtons |
| FRICTION_LIMIT_ANGLE | Peak lateral slip angle at FZ0 | degrees |

#### Load Sensitivity
Two methods — formula-based or LUT-based:

**Formula-based** (used by C6/180SX drift tires):
- `LS_EXPY`, `LS_EXPX`: Exponential parameters
- `DX_REF`, `DY_REF`: Reference mu at FZ0

**LUT-based** (used by AE86, E46, C6 performance tires):
- `DY_CURVE`, `DX_CURVE`: LUT files mapping load (N) → mu
- When using LUT: set `LS_EXPY=0, LS_EXPX=0, DX_REF=0, DY_REF=0`

#### Camber Sensitivity
- `CAMBER_GAIN`: Slip angle shift from camber: `CAMBER_GAIN * sin(camber)`
- `DCAMBER_0`, `DCAMBER_1`: Formula parameters: `1 / (1 + camberRAD*DCAMBER_0 - camberRAD²*DCAMBER_1)`
- `DCAMBER_LUT`: LUT-based (degrees → grip %, e.g., 1.05 = 105%)

#### Pressure Effects
- `PRESSURE_STATIC`: Cold nominal pressure (psi)
- `PRESSURE_IDEAL`: Optimal hot pressure for grip (psi)
- `PRESSURE_SPRING_GAIN`: Spring rate gain per psi from PRESSURE_STATIC
- `PRESSURE_D_GAIN`: Grip loss per psi deviation from PRESSURE_IDEAL

#### Falloff and Dropoff
- `FALLOFF_LEVEL`: Grip at infinite slip ratio (e.g., 0.68 = 68%)
- `FALLOFF_SPEED`: Speed of grip dropoff after peak slip
- `DROPOFF_FACTOR_0`, `DROPOFF_FACTOR_1`: Extended dropoff control (Cphys)
- `FALLOFF_LEVEL_CURVE`, `FALLOFF_SPEED_CURVE`: Temperature-dependent LUTs

#### Combined Slip
- `COMBINED_FACTOR`: Combined lat+long grip gain. 2.0 = circle, >2.0 = squarer
- `CX_MULT`: Optimal slip ratio scaling. `tan(slip_angle_opt) / CX_MULT`
- `BRAKE_DX_MOD`: Braking grip modifier. `(1+BRAKE_DX_MOD)*D`

#### Self-Aligning Torque (SAT) — Cphys
- `SAT_MULT`, `SAT_SPEED`, `SAT_PEAK_K`, `SAT_MULT_K`, `SAT_MIN_REF`, `SAT_LOAD_K`
- Controls steering feel and FFB character
- Used by AE86, 180SX (Greeva 08D tire set), C6 (performance tires)

#### Thermal Model
Two versions:
- **VERSION=1**: Basic (AE86)
- **VERSION=2**: Extended with carcass model (E46, C6, 180SX)

Key thermal parameters:
- `SURFACE_TRANSFER`: How fast asphalt heats tread (0-1)
- `FRICTION_K`: Slip → heat conversion
- `PERFORMANCE_CURVE`: Temperature vs grip LUT
- `CARCASS_ROLLING_K`: Carcass heating from rolling
- `BRAKE_TO_CORE`: Heat transfer from brakes to core

### 1.4 drivetrain.ini

#### VERSION
- Use `3` for full features

#### Differential Types
- Standard: `POWER`, `COAST`, `PRELOAD`
- `POWER=1.0 + COAST=1.0` = welded/spool (use 0.999 for "100%" clutch)
- Open diffs: 0.03-0.10 effective lock from friction

#### Viscous LSD (Cphys)
- Used by E46 M3
- `VISCOUS_FACTOR_1=157`: Linear coefficient
- Formula: `torque = VF1*Δω + VF2*Δω² + (VF_EXP_K - VF_EXP_K/exp(VF_EXP*Δω))`

#### AE86 Diff: Uses ramp-angle LSD
- `RAMP_POWER=3`, `RAMP_COAST=4`
- `RAMP_LOCK_LUT=drivetrain_diff_ramp.lut`

### 1.5 engine.ini
- `POWER_CURVE`: LUT of RPM|Torque(Nm) **at the wheels after drivetrain loss**
- `COAST_CURVE=FROM_COAST_REF`: Use coast reference
- `COAST_REF`: RPM and Torque for coasting (engine braking)
- Turbo: `T*(1.0 + boost)` — at boost=1.0, torque doubles

### 1.6 LUT Files

| LUT Type | Input | Output | Purpose |
|----------|-------|--------|---------|
| car_steerdeg_racktravel | steering wheel degrees | rack travel (meters) | Non-linear steering |
| suspensions_springs_*.lut | position | rate | Progressive springs |
| suspensions_stabilizer_*.lut | position | rate | Progressive ARB |
| dampers_*_bs/rs_*.lut | velocity | force | Damper curves |
| bumpstops_bumprubber_*.lut | displacement | force | Bumpstop curves |
| tire_*_lat/long.lut | load (N) | mu | Tire load sensitivity |
| tire_camber_dy_*.lut | camber (degrees) | grip mult | Camber sensitivity |
| tire_heat_road_*_mu.lut | temperature | grip mult | Thermal performance |
| tire_wear_dy_road_*.lut | virtual km | grip % | Tire wear |
| brakes_mu_*.lut | temperature | mu | Brake pad friction |
| brakes_booster.lut | pedal input | boost factor | Brake booster |
| drivetrain_diff_*.lut | various | various | Diff behavior |

---

## 2. Ryan's 4 Cars — Detailed Analysis

### 2.1 Toyota AE86 Sprinter Trueno (Drift)

**Overview**: Lightweight 1980s Toyota, drift configuration with modified steering

| Parameter | Value | Notes |
|-----------|-------|-------|
| TOTALMASS | 1000 kg | 925 dry + 75 driver |
| Suspension F/R | COSMIC (Strut front / Live axle rear) | |
| STEER_LOCK | 570° | Drift setup (stock PS/GT-V = 540°) |
| STEER_RATIO | 13.80 | Drift (stock = 16.30) |
| LINEAR_STEER_ROD_RATIO | -0.001674 | Calculated: -0.001977/16.30*13.80 |
| RACK_TRAVEL_LUT | Yes | car_steerdeg_racktravel.lut |
| WHEELBASE | 2.400m | |
| CG_LOCATION | 0.600 | 60% front (sprung) |
| F Spring Rate | 78480 N/m | At coilover (INSTALL_RATE=16670000 = rigid) |
| R Spring Rate | 58860 N/m | Separated spring/damper |
| F ARB | 14474 N/m (wheelrate, EXTEND=1 MR=1.0) | |
| R ARB | 1555 N/m | Very soft rear ARB |
| Tires | 185/55R14 | RE710 front, GLOBA rear |
| Tire FZ0 | 3000 N | |

**Steering derivation**: Original car has LINEAR_STEER_ROD_RATIO of -0.001977 at ratio 16.30. When changing to 13.80 ratio: `-0.001977 / 16.30 * 13.80 = -0.001674`. This is a SCALING operation — the rack travel per degree of wheel changes proportionally to the ratio change.

**Rear suspension**: COSMIC live axle with:
- Axle body (R_AE86_AXLE, mass=66.3kg — this is total axle mass)
- Upper arm (DJ0), Lower trailing arm (DJ1), Panhard rod (DJ2)
- Adjustable panhard and LCA heights via sliders
- Separate spring and damper mounting points (spring on UCA, damper separately)
- ENGINE_TORQUE_BODY=R_AE86_AXLE (axle receives engine torque reaction)

**Front suspension**: COSMIC MacPherson strut with:
- Strut body with camber/caster/height joints
- LCA with front and rear pickup points
- Tie rod (STEER_JOINT_0) with HIGH and LOW positions for Ackermann adjustment
- NCRCA (Non-Concentric Roll Center Adapter) offsets noted in comments

### 2.2 BMW M3 (E46) Coupe

**Overview**: Premium sport sedan with factory DWB2 suspension approach

| Parameter | Value | Notes |
|-----------|-------|-------|
| TOTALMASS | 1583.2 kg | Complex: 1520+75-63*0.75*0.25 (fuel adjustment) |
| Suspension F/R | COSMIC (Strut front / Multi-link rear "HA3") | |
| STEER_LOCK | 540° | Stock M3 |
| STEER_RATIO | 15.4 | Stock M3 |
| LINEAR_STEER_ROD_RATIO | 0.002155 | Positive = rack behind axle |
| RACK_TRAVEL_LUT | No | Uses DWB2-style linear ratio only |
| USE_DWB2 | 1 | Only car using this |
| WHEELBASE | 2.731m | |
| CG_LOCATION | 0.5112 | Near 50/50 |
| F Spring Rate | 27145 N/m | EU M3 spec |
| R Spring Rate | Progressive (LUT) | 66548-126548 N/m range |
| F ARB | 33557 N/m | |
| R ARB | 7692 N/m | |
| Tires | 225/45ZR18 F, 255/40ZR18 R | Michelin PS4S |
| Tire FZ0 | 3000 N | |

**Unique features**:
- **Bushing compliance modeled**: FRONT_SPRING_0 (2000 N/m) + FRONT_DAMPER_0 (160 N/m/s) for slide bushings
- **Rear bushings**: REAR_SPRING_0 (6000 N/m) + REAR_DAMPER_0 (480 N/m/s)
- **Rear spring is progressive**: Uses `SPRING_LUT` file
- **Viscous LSD**: VISCOUS_FACTOR_1=157 with minimal mechanical lock (0.05)
- **Detailed mass breakdown**: Component-by-component in comments

**Rear HA3 multi-link**: 
- Upper control arm as separate body (R_HA3_UCA_BODY, 4.695kg)
- Elastic body for trailing arm bushing compliance (R_HA3_Elastic_body, 0.285kg)
- Spring and damper on SEPARATE mounting points with different motion ratios
- Spring MR ≈ 0.623², Damper MR ≈ 1.086²

### 2.3 Nissan 180SX (Drift)

**Overview**: S13 chassis drift car with subframe flex simulation

| Parameter | Value | Notes |
|-----------|-------|-------|
| TOTALMASS | 1285 kg | 1210 dry + 75 driver |
| Suspension F/R | COSMIC (Strut front / Multi-link rear with subframe) | |
| STEER_LOCK | 558° | Modified drift |
| STEER_RATIO | 14.30 | |
| LINEAR_STEER_ROD_RATIO | -0.001281 | Rack in front |
| RACK_TRAVEL_LUT | Yes | |
| WHEELBASE | 2.475m | |
| CG_LOCATION | 0.555 | |
| F Spring Rate | 78480 N/m | Same as AE86 front |
| R Spring Rate | 58860 N/m | Same as AE86 rear |
| F ARB | 26133 N/m | |
| R ARB | 5371 N/m | |
| Tires | 215/45R17 (multiple compounds) | |

**Unique features**:
- **Subframe flex simulation**: Uses VERSION=5 with _EXTENSION_FLEX
- `R_S13_SUBFRAME_BODY` (30kg) connected to chassis via 6 DJ joints
- `CHASSIS_REAR_0` and `CHASSIS_REAR_1` bodies (242.7kg each) simulate torsional flex
- `HJ0=TORSION_HINGE`: Torsion spring (6000 N/m) + damper (9580 N/m/s)
- `HJ1=PITCH_HINGE`: Pitch spring (60000 N/m) + damper (30295 N/m/s)
- `ENGINE_TORQUE_BODY=CHASSIS_REAR_0` (torque reaction through subframe)
- Multiple rear LCA height adjustments (DJ2_POS_A through DJ2_POS_A_3)
- **Multiple tire compounds**: Accelera All-Season, Armstrong, 351 Sport, 651 Sport, Greeva 08D, Winter

**Front suspension**: Very similar to AE86 COSMIC strut but with S13-specific geometry

### 2.4 Chevrolet Corvette C6 Z06

**Overview**: High-performance American sports car with DWB front and rear

| Parameter | Value | Notes |
|-----------|-------|-------|
| TOTALMASS | 1495 kg | 1420 dry + 75 driver |
| Suspension F/R | COSMIC (DWB front / DWB rear) | |
| STEER_LOCK | 500° | Stock 2005-2009 |
| STEER_RATIO | 17.1 | Linear, 2005-2009 |
| LINEAR_STEER_ROD_RATIO | 0.001967 | (0.115/(500*2))*17.1 |
| RACK_TRAVEL_LUT | Yes | |
| WHEELBASE | 2.685m | |
| CG_LOCATION | 0.530 | 53% front |
| F Spring Rate | 104680 N/m (at coilover) | Z06 spec |
| R Spring Rate | 228069 N/m (at coilover) | Z06 spec |
| F ARB | 51508 N/m | |
| R ARB | 34000 N/m | |
| Tires | Multiple: 08D, S007A, SC3R | 275F/325R for perf tires |
| Tire FZ0 | 3000 N (perf), 2330 N (drift) | |

**Unique features**:
- **True DWB front AND rear** (UCA + LCA with separate bodies)
- **LCA as separate COSMIC body**: F_C6_LCA_BODY, R_C6_LCA_BODY
- **Adjustable camber/caster via sliders**: FLCA_CAMBER, RLCA_CASTER adjusters
- **Transverse leaf spring**: Spring mounted to LCA body, not directly to hub
  - `INSTALL_RATE=340000` — leaf spring installation stiffness
  - Spring acts on LCA body, which pivots to create wheel rate
- **Bushing compliance**: FRONT_SPRING_0/REAR_SPRING_0 with detailed N/m calculations per bushing
  - E.g., Front: 8485 N/m total from 5 bushings at specific arm lengths and 133 Nm/rad
  - Formula: `bushing_rate = torque_rate / arm_length²`
- **Multiple tire compounds** spanning drift budget tires to racing tires

---

## 3. Cross-Reference Findings

### 3.1 Steering System Patterns

**LINEAR_STEER_ROD_RATIO derivation — confirmed formula:**
```
LINEAR_STEER_ROD_RATIO = ±(total_rack_travel_m / (STEER_LOCK * 2)) * STEER_RATIO
```

Verification with C6:
- Total rack travel = 0.115m (115mm)
- STEER_LOCK = 500° → total range = 1000°
- STEER_RATIO = 17.1
- `(0.115 / 1000) * 17.1 = 0.001967` ✓

Verification with AE86 (drift):
- Original LSRR at ratio 16.30 = -0.001977
- At ratio 13.80: `-0.001977 * (13.80/16.30) = -0.001674` ✓
- This means the rack travel itself doesn't change; only the ratio changes

**RACK_TRAVEL_LUT analysis:**

AE86 LUT: Step size = 2.70° (570/~211 entries), non-linear progression
- At 0°: 0.0m
- At ~570°: approximately -0.057m (57mm one side)
- Total rack travel ≈ 114mm
- The values are **negative** (rack moves toward driver for left turn)

C6 LUT: Step size = 2.50° (500/200 entries), appears LINEAR
- At 0°: 0.0m
- At 500°: approximately 0.096m
- Rate: ~0.000192 m/deg
- Total rack travel ≈ 192mm (much longer — C6 has wider track)
- Values are **positive** (opposite rack position)

**The sign of the LUT values matches the sign of LINEAR_STEER_ROD_RATIO** — this is how the game knows which direction rack travel means turning.

### 3.2 Spring Rate Patterns

**Natural frequency check** (undamped):
Formula: `fn = (1/2π) * √(wheel_rate / sprung_mass_per_corner)`

AE86 Front:
- Wheel rate ≈ 78480 N/m (COSMIC coilover, approximately 1:1 MR for strut)
- Sprung mass per front corner ≈ (1000 - 33.9*2 - 22.9*2 - 66.3) * 0.60 / 2 ≈ 241 kg
- fn ≈ (1/6.28) * √(78480/241) ≈ 2.87 Hz — **HIGH for a road car, appropriate for drift**

E46 Front:
- Wheel rate ≈ 27145 * MR² — with COSMIC strut MR, effective wheel rate lower
- Sprung mass per front corner ≈ (1583 - 47*2 - 51.5*2 - 4.7*2 - 0.3*2) * 0.511 / 2 ≈ 365 kg
- With MR ~0.88: wheel rate ≈ 27145 * 0.88² ≈ 21,017 N/m
- fn ≈ (1/6.28) * √(21017/365) ≈ 1.21 Hz — **reasonable for luxury sports**

C6 Z06 Front:
- Spring at coilover = 104680 N/m, INSTALL_RATE = 340000 (leaf spring installation)
- Effective series rate ≈ 1/(1/104680 + 1/340000) = 80,040 N/m at coilover
- Then MR from LCA pivot geometry applies
- This is complex — transverse leaf spring motion ratio depends on geometry

### 3.3 Damper Patterns

AE86 and 180SX use `DAMPER_LUTS=1` with separate LUT files for each damper setting.
E46 uses `DAMPER_LUTS=0` with the 4-parameter model (slow/fast bump/rebound).
C6 uses `DAMPER_LUTS=1`.

### 3.4 Tire Patterns

**Two tire "schools"**:

1. **Arch-method tires** (E46, C6 performance): VERSION=10/11, LUT-based load sensitivity, `LS_EXP*=0.5`, `D*_REF=0.5`, extensive SAT/dropoff parameters
2. **Drift/budget tires** (C6/180SX compounds 0-3): VERSION=11, formula-based load sensitivity, higher `LS_EXP*` (0.75-0.90), higher `D*_REF` (1.18-1.28)

The Greeva 08D tire on both C6 and 180SX is the most Arch-like of the drift tires (LUT-based, VERSION=10/11 SAT parameters).

### 3.5 COSMIC vs Standard Suspension

Ryan uses COSMIC for ALL 4 cars, even though the E46's geometry is closest to what DWB2 could handle. Benefits:
- No STRUT mass redistribution quirk
- Proper motion ratios from geometry
- Bushing compliance modeling
- Separate spring/damper mounting points
- Adjustable geometry via LENGTH_OFFSET

---

## 4. Formulas for the Tool

### 4.1 Steering

```
LINEAR_STEER_ROD_RATIO = sign * (total_rack_travel_m / (STEER_LOCK * 2)) * STEER_RATIO
```
Where `sign` = +1 if rack behind axle, -1 if rack in front.

**When changing STEER_RATIO but keeping the same rack:**
```
new_LSRR = old_LSRR * (new_ratio / old_ratio)
```

**When changing STEER_LOCK but keeping the same rack and ratio:**
The rack travel per degree changes — need to regenerate the LUT.

**Rack travel LUT generation:**
For linear rack: `rack_travel = steer_degrees / STEER_RATIO * LSRR_per_deg`
But the LUT is specifically: `steer_wheel_degrees | rack_travel_meters`
The step size is typically `STEER_LOCK / num_entries`.

### 4.2 CG Height

```
BASEY = -(loaded_tire_radius - CGH)
```
Wait — let me re-derive from Arch:
> "A negative BASEY produces a positive CGH. The formula is RADIUS - BASEY."

So: `CGH = RADIUS - BASEY`
Since BASEY is negative: `CGH = RADIUS - (-|BASEY|) = RADIUS + |BASEY|`

AE86: RADIUS=0.2796, BASEY=-0.250 → CGH = 0.2796 + 0.250 = 0.530m ✓ (reasonable for AE86)
E46: RADIUS=0.33, BASEY=-0.210 → CGH = 0.33 + 0.210 = 0.540m
- But E46 comment says "325i E46/4 523mm" — slight discrepancy, likely using loaded radius
C6: RADIUS≈0.325 (275 tire), BASEY=-0.170 → CGH = 0.325 + 0.170 = 0.495m
- C6 comment says "457mm CGH" — using smaller tire? Or loaded radius differs

**The loaded tire radius matters, not the unloaded RADIUS from tyres.ini.**
Loaded radius ≈ RADIUS - (static_load / RATE)

### 4.3 Spring Rate / Natural Frequency

```
fn = (1 / (2π)) * √(wheel_rate / sprung_mass_per_corner)
```

```
sprung_mass_per_corner = (TOTALMASS - total_unsprung_mass) * weight_distribution / 2
```

For front: `weight_distribution = CG_LOCATION`
For rear: `weight_distribution = 1 - CG_LOCATION`

**Wheel rate from spring rate:**
```
wheel_rate = spring_rate * motion_ratio²
```

### 4.4 ARB

With EXTEND=1 and MR=1.0:
```
ARB_wheelrate = ARB_value (direct input as wheelrate)
```

With EXTEND=1 and custom MR:
```
ARB_wheelrate = ARB_springrate * MR²
```

Without EXTEND:
```
ARB_wheelrate = ARB_value (already wheelrate)
```

### 4.5 Tire Spring Rate vs Pressure

```
actual_tire_rate = RATE + (current_pressure - PRESSURE_STATIC) * PRESSURE_SPRING_GAIN
```

---

## 5. What the Tool Currently Gets WRONG

### 5.1 CRITICAL: Suspension Geometry Cannot Be Calculated from Specs
The tool CANNOT generate COSMIC suspension coordinates from car specifications. These require:
- Actual CAD data or careful measurements
- Knowledge of kingpin inclination, caster angle, scrub radius
- Ball joint locations, control arm lengths, strut inclination angles
- These are VEHICLE-SPECIFIC and cannot be derived from basic specs

### 5.2 CRITICAL: Spring Rates Need Motion Ratio
The relationship between coil spring rate and wheel rate depends on:
- The exact mounting position of the spring
- The suspension geometry (lever arm lengths)
- For COSMIC, this is solved kinematically — the RATE in the coilover IS the spring rate
- For standard suspensions, SPRING_RATE IS the wheel rate
- **The tool should NOT try to convert between the two without knowing motion ratio**

### 5.3 CRITICAL: Rack Travel LUT is Geometry-Dependent
The rack travel LUT maps steering wheel angle to physical rack displacement.
- For a linear rack, it's straightforward: `travel = angle / ratio * linear_factor`
- For non-linear racks, it requires steering geometry data
- The AE86 LUT shows slight non-linearity; C6 is nearly linear
- **Cannot generate this from scratch without knowing rack geometry**

### 5.4 LINEAR_STEER_ROD_RATIO Sign
- Depends on whether the steering rack is in front of or behind the wheel center
- Front rack (AE86, 180SX) = negative sign
- Rear rack (E46, C6) = positive sign
- **Tool must ask or determine rack position**

### 5.5 HUB_MASS Breakdown
- Cannot be auto-calculated without component weights
- Varies dramatically: 22.9kg (AE86 rear) to 58kg (C6 rear)
- Must include: wheel, tire, brake, knuckle, portion of driveshaft, bearings, etc.
- Ryan provides detailed component breakdowns in comments

### 5.6 Inertia Values
- Sprung inertia ≠ total car inertia
- Requires knowing or estimating total inertia then subtracting unsprung contribution
- No simple formula from dimensions alone

---

## 6. Do NOT Auto-Calculate (Needs Geometry Data)

1. **ALL suspension coordinate points** (DJ, J, SLIDER positions)
2. **BODY positions and masses** for COSMIC bodies
3. **Motion ratios** (kinematically solved from geometry)
4. **Rack travel LUT** (needs physical rack geometry)
5. **LINEAR_STEER_ROD_RATIO** magnitude (needs total rack travel measurement)
6. **LINEAR_STEER_ROD_RATIO sign** (needs rack position: front or behind)
7. **BASEY** precise value (needs accurate loaded tire radius and CGH)
8. **HUB_MASS** per corner (needs component-level data)
9. **INERTIA** box dimensions (needs vehicle-specific data or solver)
10. **Bumpstop/packer gaps** (depend on suspension travel and geometry)
11. **Bushing spring rates** (FRONT_SPRING_0 etc.) — need bushing specs
12. **INSTALL_RATE** — depends on spring mounting method
13. **Camber/caster/toe LENGTH_OFFSET values** — alignment-specific

---

## 7. CAN Safely Auto-Calculate

1. **TOTALMASS** = dry_weight + 75 (driver)
2. **Gear ratios** — from manufacturer specs, direct input
3. **STEER_LOCK** — from manufacturer specs (total lock-to-lock / 2)
4. **STEER_RATIO** — from manufacturer specs
5. **WHEELBASE** — from manufacturer specs
6. **Tire dimensions**: RADIUS, WIDTH, RIM_RADIUS from tire size code
7. **FUEL tank parameters** — MAX_FUEL from specs
8. **Engine power curve** — from dyno data if available
9. **ANGULAR_INERTIA** — approximate from wheel+tire+brake mass and radius
10. **Tire RATE** — approximate from tire dimensions and pressure
11. **PRESSURE_STATIC/IDEAL** — from manufacturer recommendations
12. **CONSUMPTION** — approximate from engine specs
13. **Differential type and lock %** — from manufacturer specs
14. **CG_LOCATION** — from manufacturer weight distribution (but remember: this is SPRUNG, not total)
15. **Rough natural frequency check** — validate spring rates make sense
16. **Scaling LSRR when only ratio changes** — `new = old * (new_ratio / old_ratio)`

---

## 8. How Steering Modifications Actually Work

### 8.1 The Steering Chain

The AC steering system works as follows:

```
User wheel input (0-100%)
    ↓
STEER_LOCK (maps % to degrees)
    ↓
RACK_TRAVEL_LUT or LINEAR_STEER_ROD_RATIO (maps degrees to rack travel)
    ↓
Rack travel displaces tie rod (STEER_JOINT_0)
    ↓
WBCAR_STEER/WBTYRE_STEER geometry (converts rack travel to wheel angle)
    ↓
Actual road wheel angle
```

### 8.2 What Each Parameter Does

**STEER_LOCK**: Only controls how much the in-cockpit wheel rotates. Changing this alone changes the **ratio of input to output** but doesn't change maximum wheel angle (that's limited by geometry/rack travel).

**STEER_RATIO**: Used WITH LINEAR_STEER_ROD_RATIO to calculate rack travel per degree. Changing ratio changes how much rack moves per degree of wheel rotation.

**LINEAR_STEER_ROD_RATIO**: The master parameter. It directly determines how many meters the rack moves per degree of steering wheel rotation (scaled by STEER_RATIO).

**RACK_TRAVEL_LUT**: When present, OVERRIDES the LINEAR_STEER_ROD_RATIO calculation. The LUT directly maps steering wheel degrees to rack travel meters.

### 8.3 Modifying Steering Angle

**Scenario: Increasing maximum steering angle for drift**

There are THREE ways this can happen in real life and in AC:

#### Method 1: Change Steering Ratio (Quick Ratio Rack)
- Real life: Install a different rack with more travel per turn
- In AC: Change STEER_RATIO, recalculate LINEAR_STEER_ROD_RATIO
- `new_LSRR = old_LSRR * (new_ratio / old_ratio)`
- If using RACK_TRAVEL_LUT: Regenerate with new rate of travel per degree
- Wheel angle increases because rack moves more per degree of wheel input

#### Method 2: Change Steering Lock (More Wheel Rotation)
- Real life: Remove steering stops, modify column
- In AC: Change STEER_LOCK
- LINEAR_STEER_ROD_RATIO stays the same (rack travel per degree unchanged)
- RACK_TRAVEL_LUT needs entries extended to the new lock angle
- More wheel turns = more total rack travel = more wheel angle
- **Important**: The LUT must cover the full range of STEER_LOCK

#### Method 3: Change Suspension Geometry (Spacers, Knuckles, etc.)
- Real life: Rack spacers, extended tie rod ends, different knuckles (Wisefab, etc.)
- In AC: Change STEER_JOINT_0 coordinates (WBCAR_STEER/WBTYRE_STEER)
- This changes the Ackermann geometry and how rack travel translates to wheel angle
- The same rack travel produces MORE wheel angle with longer steering arms
- **Cannot be auto-calculated** — needs geometry data

### 8.4 Ryan's AE86 Drift Steering Example

The AE86 shows all three methods in action:
1. **Ratio change**: Stock 16.30 → Drift 13.80 (quicker ratio)
2. **Lock change**: Stock 540° → Drift 570° (more rotation)
3. **Geometry change**: "Rack spacers +30deg" — physical modification to steer joint positions
4. **NCRCA** (Non-Concentric Roll Center Adapter): Changes LCA geometry, affecting steering axis

The LSRR calculation: `-0.001977 / 16.30 * 13.80 = -0.001674`
This ONLY accounts for the ratio change. The rack spacers and geometry changes are handled by the COSMIC joint positions.

### 8.5 CSP Steering Torsion Bar

Not observed in Ryan's cars, but mentioned in context:
- CSP can add steering shaft torsion (flex/compliance)
- Simulates steering column elasticity
- Controlled via extension config, not core physics files

### 8.6 Tool Implications for Steering

**What the tool CAN do:**
- Accept STEER_LOCK, STEER_RATIO as user inputs
- Calculate LINEAR_STEER_ROD_RATIO if total rack travel is known
- Scale LSRR when only the ratio changes (keeping same rack)
- Generate a LINEAR rack travel LUT from STEER_LOCK and a constant rate
- Warn if RACK_TRAVEL_LUT doesn't cover the full STEER_LOCK range

**What the tool CANNOT do:**
- Generate non-linear rack travel LUTs from scratch
- Determine the sign of LSRR without knowing rack position
- Calculate actual wheel angle from rack travel (geometry-dependent)
- Model steering modifications that involve geometry changes (Wisefab, rack spacers, etc.)
- Determine total rack travel without measurement data

### 8.7 The Reference steer_deg_rack_travel.lut

The reference file in the project directory appears to be a generic template:
- 192+ lines covering roughly 0-340° per side
- Step size ≈ 2.65°
- Rate ≈ 0.000157 m/deg (approximately linear)
- At 129.61°: travel = 0.02156m (21.6mm)
- This is likely the E46 rack data scaled/templated

---

## Appendix A: File Format Quick Reference

### Required Files in data/ folder:
- `car.ini` — core vehicle parameters
- `suspensions.ini` — suspension geometry and springs/dampers
- `tyres.ini` — tire model
- `drivetrain.ini` — gears and differential
- `engine.ini` — power and coast curves
- `brakes.ini` — brake torque model
- `aero.ini` — aerodynamic forces
- `setup.ini` — in-game adjustable parameters
- Various `.lut` files referenced by the above

### COSMIC-Specific Observations from Ryan's Cars:
- All use `ELECT_LOG=CORNER` on coilovers for telemetry
- `PULL_FORCE=0` on all springs (no tension springs)
- `PRELOAD_FORCE` sets the static preload force
- `PRELOAD` is the displacement from design height (negative = compressed)
- `MIN_LENGTH` / `MAX_LENGTH` define coilover travel limits
- `INSTALL_RATE` high value (16.67M) = rigid mount, lower (340k, 1M) = compliant

### Suspension Version Summary:
| Car | sus VERSION | TORQUE_MODE_EX | USE_DWB2 | DAMPER_LUTS | FLEX |
|-----|------------|----------------|----------|-------------|------|
| AE86 | 4 | 2 | 0 | 1 | No |
| E46 | 4 | 2 | 1 | 0 | No |
| 180SX | 5 | 2 | 0 | 1 | Yes |
| C6 | 5 | 2 | 0 | 1 | Yes |

---

## Appendix B: Common Values Reference

### Typical Natural Frequencies:
- Luxury/comfort: 1.0-1.3 Hz
- Sport/touring: 1.3-1.8 Hz
- Track/race: 1.8-2.5 Hz
- Drift: 2.5-3.5 Hz
- Formula car: 3.0-5.0+ Hz

### Typical Damping Ratios:
- Comfort: 0.2-0.3
- Sport: 0.3-0.5
- Race: 0.5-0.7
- Critical: 1.0

### Tire FZ0 Reference:
- Ryan uses FZ0=3000N for most performance/drift tires
- FZ0=2330N for budget drift tires (lighter load expectation)
- FZ0=970N for winter tires

### Steering Ratios:
- Quick rack (sport/drift): 12-15:1
- Standard: 15-17:1
- Slow (truck/luxury): 17-20:1

### Typical Total Rack Travel:
- Compact car: 100-130mm
- Sport car: 110-150mm
- Truck/SUV: 150-200mm
- The C6 Corvette has ~192mm (wider track needs more travel)
