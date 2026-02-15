-- Main modular script loader

local function safe_require(name)
    local ok, mod = pcall(require, name)
    if not ok then
        ac.log("Module not found: " .. name)
        return nil
    end
    return mod
end

local sim_throttle_model = safe_require("script_sim_throttle_model")
local sim_turbo_ref_model = safe_require("script_sim_turbo_ref_model")
local sim_clutch_model = safe_require("script_sim_clutch_model")
local dccd = safe_require("script_dccd")

function script.update(dt)
    if type(sim_throttle_model) == "table" and sim_throttle_model.runThrottleModel then
        sim_throttle_model.runThrottleModel()
    end

    if type(sim_turbo_ref_model) == "table" and sim_turbo_ref_model.runTurboRefModel then
        sim_turbo_ref_model.runTurboRefModel()
    end

    if type(sim_clutch_model) == "table" and sim_clutch_model.runClutchModel then
        sim_clutch_model.runClutchModel()
    end

    if type(dccd) == "table" and dccd.rundccd then
        dccd.rundccd(dt)
    end
end