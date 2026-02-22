# AiO Drift Physics Swap — How It Works

## Overview

The Drift Physics Exchange takes your Assetto Corsa car and swaps its physics with a professional drift carpack. Your car keeps its identity (name, 3D model, visual offsets, dimensions) while receiving an entirely new physics package (suspension geometry, tuning, engine, drivetrain, tyres, aero, etc).

**The golden rule:** The donor carpack provides the *physics*. Your original car provides the *identity and dimensions*.

---

## What Your Original Car Keeps

These values are unique to your car's 3D model and physical dimensions. Changing them would break the visual alignment or make the car behave incorrectly for its size.

### car.ini

| Section | Key | Why It Stays |
|---------|-----|-------------|
| `[HEADER]` | `VERSION` | Your car's format version (exception: BDC packs override this with `extended-2`) |
| `[INFO]` | Entire section | Car name, screen name — it's still your car |
| `[BASIC]` | `TOTALMASS` | Your car's actual weight |
| `[BASIC]` | `INERTIA` | Rotational inertia — tied to your car's mass distribution and size |
| `[BASIC]` | `GRAPHICS_OFFSET` | X and Z offsets (horizontal/longitudinal position of the 3D model). **Y (height) comes from the donor** because suspension geometry changes ride height |
| `[BASIC]` | `GRAPHICS_PITCH_ROTATION` | Visual pitch of the 3D model |
| `[GRAPHICS]` | Entire section | Camera positions, driver eye position, mirror position — all tied to your car's 3D model |
| `[RIDE]` | Entire section | Pickup truck heights — geometry-dependent |

### suspensions.ini

| Section | Key | Why It Stays |
|---------|-----|-------------|
| `[BASIC]` | `WHEELBASE` | Distance between front and rear axles — a physical measurement of your car |
| `[BASIC]` | `CG_LOCATION` | Center of gravity position along the wheelbase — tied to your car's weight distribution |
| `[FRONT]` | `TRACK` | Front track width — how far apart the front wheels are |
| `[REAR]` | `TRACK` | Rear track width — how far apart the rear wheels are |
| `[GRAPHICS_OFFSETS]` | Entire section | Visual positions of wheels and suspension components (WHEEL_LF, SUSP_LF, WHEEL_RF, SUSP_RF, WHEEL_LR, SUSP_LR, WHEEL_RR, SUSP_RR) — tied to your car's 3D model |

### tyres.ini

| Section | Key | Why It Stays |
|---------|-----|-------------|
| All `[FRONT*]` | `RADIUS` | Outer tyre radius — must match your car's wheel wells |
| All `[FRONT*]` | `RIM_RADIUS` | Rim size — must match your car's wheels |
| All `[REAR*]` | `RADIUS` | Same as above, rear |
| All `[REAR*]` | `RIM_RADIUS` | Same as above, rear |

---

## What Comes From the Donor Carpack

Everything else. This is the actual *physics* — how the car drives, grips, slides, and sounds mechanically.

### car.ini
- `[CONTROLS]` — Steering lock, steer ratio, force feedback multiplier, linear steer rod ratio
- `[FUEL]` — Fuel consumption rates
- `[FUELTANK]` — Tank capacity and position
- `[PIT_STOP]` — Pit stop configuration
- `[HEADER]` — Only for BDC packs (uses `VERSION=extended-2`)

### suspensions.ini
- **Everything** except WHEELBASE, CG_LOCATION, TRACK, and GRAPHICS_OFFSETS
- This includes: suspension type, spring rates, dampers, ARB, bump stops, camber, toe, rod length, all WB* connection points (steering geometry, wishbone attach points), BASEY, RIM_OFFSET, HUB_MASS, packer range, all `[DAMAGE]`, `[ARB]`, `[HEADER]`, `[_EXTENSION*]` sections

### tyres.ini
- **Everything** except RADIUS and RIM_RADIUS
- This includes: WIDTH, all grip curves, thermal model, wear curves, compound names, compound count, all `[THERMAL_*]` sections, `[HEADER]`, `[COMPOUND_DEFAULT]`

### Full replacement files (entire file from donor)
- `engine.ini` — Engine power, torque, RPM range, turbo/NA config
- `drivetrain.ini` — Gearbox, differential, clutch, final drive
- `brakes.ini` — Brake force, balance, disc size
- `electronics.ini` — ABS, traction control, stability
- `aero.ini` — Downforce, drag, wing configuration
- `setup.ini` — Default setup values
- `damage.ini` — Damage model
- `drs.ini` — DRS configuration (if exists)
- `escmode.ini` — ESC modes (if exists)

### All .lut and .rto files from donor
- `power.lut` — Engine power curve
- `engine_map*.lut` — Engine maps
- `throttle.lut` — Throttle response
- All tyre thermal/wear curve .lut files
- All wing/aero .lut files
- `ratios.rto`, `final.rto` — Gear ratios

---

## Advanced Options

### Manual Donor Car Selection
By default, the tool auto-matches the closest donor car based on weight + wheelbase + track width. You can override this in Advanced Settings to pick any car from the selected pack.

### Engine Source Override
You can use one car's chassis physics but another car's engine. When you select a different engine source:
- `engine.ini`, `drivetrain.ini`, `power.lut`, `engine_map*.lut`, and `throttle.lut` come from the engine source car
- Everything else still comes from the primary donor car

---

## Files NEVER Included (stay original — visual/model files)

These are part of your car's 3D model and visuals. They are never touched:

- `colliders.ini`, `ambient_shadows.ini`, `cameras.ini`, `lods.ini`
- `sounds.ini`, `lights.ini`, `mirrors.ini`, `driver3d.ini`
- `suspension_graphics.ini`, `blurred_objects.ini`
- `analog_instruments.ini`, `digital_instruments.ini`
- `dash_cam.ini`, `flames.ini`, `wing_animations.ini`
- `ai.ini`, `proview_nodes.ini`
- All 3D models, textures, skins

---

## BDC Pack Special Case

BDC v4 and BDC v6 use `VERSION=extended-2` in their `[HEADER]` section. When swapping with a BDC pack, the donor's header is used instead of the original car's header. This is required for the extended physics features in BDC packs to function correctly.

---

## Output

The tool generates a ZIP file named `data_<packname>.zip` (e.g., `data_BDC.zip`, `data_WDTS.zip`). Files are at the root of the ZIP — extract directly into your car's `data/` folder to apply the swap. Your original files are replaced, so keep a backup if you want to revert.

---

*Built by RealiSimHQ — Drift Physics Exchange*
*https://realisimhq.github.io/ac-physics-tool/*
