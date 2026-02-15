-- script_sim_turbo_ref_model.lua — RealiSimHQ Turbo Logic (Safe)

local engine_ini = ac.INIConfig.carData(0, "engine.ini")
local drivetrain_file = ac.INIConfig.carData(0, "drivetrain.ini")
local turbo_data = {}
local gear_ratios = {}
local ref_rpm_by_gear = {}
local final_drive_ratio
local gear_ratio_closest_to_1
local current_gear = 1
local last_gear = 1
local initialized = false

local function detectTurbos()
    local count = ac.getCar(0).turboCount or 0
    if count < 1 then return false end
    for i = 0, count - 1 do
        turbo_data[i+1] = {
            max_boost = engine_ini:get('TURBO_'..i, 'MAX_BOOST', 0),
            ref_rpm = engine_ini:get('TURBO_'..i, 'REFERENCE_RPM', 3000),
            lag_up = engine_ini:get('TURBO_'..i, 'LAG_UP', 0.99),
            lag_dn = engine_ini:get('TURBO_'..i, 'LAG_DN', 0.99),
            gamma = engine_ini:get('TURBO_'..i, 'GAMMA', 1.5)
        }
    end
    return true
end

local function getGearRatios()
    local physics = ac.getCarPhysics(0)
    local ratios = physics and physics.gearRatios or {}
    gear_ratios = {}
    for i = 1, #ratios do
        if ratios[i] then
            table.insert(gear_ratios, math.round(ratios[i], 3))
        end
    end
    local default_final = drivetrain_file:get("GEARS", "FINAL", 3)
    local final_drive = physics and physics.finalRatio or 1
    final_drive_ratio = math.round(default_final / final_drive, 3)
end

local function closestToOne()
    local minDiff = math.huge
    for _, r in ipairs(gear_ratios) do
        local diff = math.abs(1 - r)
        if diff < minDiff then
            gear_ratio_closest_to_1 = r
            minDiff = diff
        end
    end
end

local function boostExponent(ratio, boost)
    return (0.07625 * boost^2 + 0.07126 * boost + 1.052) ^ (ratio * final_drive_ratio)
end

local function calculateRefRPMs()
    for i, t in ipairs(turbo_data) do
        local base = t.ref_rpm / boostExponent(gear_ratio_closest_to_1, t.max_boost)
        ref_rpm_by_gear[i] = {}
        for g, r in ipairs(gear_ratios) do
            ref_rpm_by_gear[i][g] = math.round(base * boostExponent(r, t.max_boost))
        end
    end
end

local function updateTurbos(gear)
    for i, t in ipairs(turbo_data) do
        local rpm = ref_rpm_by_gear[i][gear] or t.ref_rpm
        ac.setTurboExtras2(i-1, t.lag_up, t.lag_dn, rpm, t.gamma)
    end
end

local sim_turbo_ref_model = {}
function sim_turbo_ref_model.runTurboRefModel()
    if not initialized then
        if not detectTurbos() then return end
        getGearRatios()
        if #gear_ratios == 0 then ac.log("⚠️ No gear ratios found. Turbo script skipped.") return end
        closestToOne()
        calculateRefRPMs()
        initialized = true
    end
    current_gear = ac.getCar(0).gear
    if current_gear ~= last_gear then
        updateTurbos(current_gear)
        last_gear = current_gear
    end
end

return sim_turbo_ref_model
