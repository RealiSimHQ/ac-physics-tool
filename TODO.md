# AC Physics Tool — TODO

## UI / UX
- [ ] Parts ordered from lowest to highest upgrade tier (not random)
- [ ] FWD / RWD / AWD drivetrain selector
  - Ryan has a Lua script for live diff swapping in AWD cars (waiting on file)

## Engine Swaps
- [ ] Engine HP values must represent REAL engine output (not placeholder numbers)
- [ ] Engine swaps affect car weight (heavier engines = more mass, lighter = less)
- [ ] Need accurate weight delta per engine swap

## Turbo System
- [ ] Add turbo option — simple sizes (small/medium/large), NOT brands
- [ ] Turbo modifies: power.lut + engine.ini + [TURBO_0] section in engine.ini
- [ ] All three interact for HP/torque calculations — must be done together
- [ ] Research: how AC turbo parameters (MAX_BOOST, WASTEGATE, LAG_DN/UP, REFERENCE) map to real turbo sizing

## Physics Accuracy (from PHYSICS_KNOWLEDGE.md)
- [ ] Tool reads EXISTING data and modifies (not generating from zero)
- [ ] Can adjust hub mass when adding parts (brake kits, angle kits add weight)
- [ ] Can scale rack travel LUT for steering ratio changes
- [ ] Can read and preserve suspension geometry while changing spring/damper values
- [ ] LSRR adjustment when ratio changes: `new = old × (new_ratio / old_ratio)`
- [ ] Spring rate changes need to account for COSMIC vs standard suspension differences
- [ ] STEER_LOCK formula: confirmed wrong, needs proper implementation

## Waiting On
- [ ] Ryan's AWD diff swap Lua script
- [ ] More research on turbo parameter relationships
- [ ] Proper steering geometry implementation (after physics research is solid)
