# AC Physics Tool — TODO

## Core Architecture
- [ ] Tool reads existing data folder → detects car + suspension type → shows valid options → outputs modified files
- [ ] Every modification cascades properly (RWD swap → new drivetrain.ini + CoG shift + weight change)
- [ ] Generate complete setup.ini with correct adjustable ranges per suspension type + installed mods
- [ ] Setup ranges = realistic min/max/default/step (what you'd see in AC setup screen)

## Suspension Type Detection & Options
- [ ] Detect suspension type from suspensions.ini (STRUT, DWB, ML, AXLE, COSMIC variants)
- [ ] Each type gets different adjustable parameters:
  - DWB front: can change steer ratio, camber, caster, toe, ride height, springs, dampers, ARB
  - STRUT front: NO steer ratio change, camber/toe/ride height/springs/dampers/ARB
  - Solid rear axle: NO camber/caster/toe adjustment
  - Need to research: COSMIC — does it inherit base type limitations?
- [ ] Show only realistic options for detected suspension type
- [ ] Setup.ini values = the "settled" values AC shows after calculation (right-hand window)

## Drivetrain
- [ ] FWD / RWD / AWD selector
- [ ] RWD swap: changes drivetrain.ini, affects CoG (engine/trans weight shifts), weight delta
- [ ] AWD swap: includes DCCD system (Lua + controller INIs + drivetrain [AWD] section)
- [ ] Ryan has DCCD Lua + controller INIs saved in lua_scripts/

## Engine Swaps
- [ ] Engine HP values must represent REAL engine output
- [ ] Engine swaps affect car weight (weight delta per engine)
- [ ] Engine swap affects CoG position (different engine = different mass distribution)

## Turbo System
- [ ] Add turbo option — simple sizes (small/medium/large), NOT brands
- [ ] Turbo modifies: power.lut + engine.ini + [TURBO_0] section together
- [ ] All three interact for HP/torque calculations — must be done as a unit
- [ ] Research: how MAX_BOOST, WASTEGATE, LAG_DN/UP, REFERENCE map to real turbo sizing

## UI / UX
- [ ] Parts ordered from lowest to highest upgrade tier
- [ ] Before/after stats optional/collapsible
- [ ] Brand-first parts naming (compatibility filtered behind the scenes)
- [ ] Two paths: Quick Build (class tiers) + Custom Build (individual parts)

## Physics Accuracy
- [ ] Tool reads EXISTING data and modifies (not generating from zero)
- [ ] Can adjust hub mass when adding parts (brake kits, angle kits add weight)
- [ ] Can scale rack travel LUT for steering ratio changes (DWB only)
- [ ] Can read and preserve suspension geometry while changing spring/damper values
- [ ] LSRR adjustment when ratio changes: `new = old × (new_ratio / old_ratio)`
- [ ] Spring rate changes need to account for COSMIC vs standard differences
- [ ] Steering geometry: only modify on DWB front ends

## Research Needed
- [ ] COSMIC suspension: does it inherit base type limitations? (steer ratio, adjustability)
- [ ] How setup.ini "settled values" are calculated from raw parameters
- [ ] Turbo parameter relationships in AC
- [ ] Weight deltas for common engine swaps
- [ ] CoG shift formulas when swapping drivetrain layout

## Reference Files
- lua_scripts/script_dccd.lua — DCCD controller (AWD live diff adjustment)
- lua_scripts/ctrl_front_diff.ini — front diff controller for DCCD
- lua_scripts/ctrl_centre_diff.ini — centre diff controller for DCCD
- lua_scripts/script.lua — main loader (includes DCCD module)
- lua_scripts/script_sim_throttle_model.lua — throttle simulation
- lua_scripts/script_sim_turbo_ref_model.lua — turbo reference model
- lua_scripts/script_sim_clutch_model.lua — clutch simulation
- reference/drivetrain_awd_example.ini — full AWD drivetrain config
- reference/final_ratio.lut — selectable final drive ratios (8.00→1.00)
- reference/steer_deg_rack_travel.lut — steering rack displacement curve
- PHYSICS_KNOWLEDGE.md — comprehensive physics research document
