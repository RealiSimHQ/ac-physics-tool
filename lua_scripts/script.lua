-- ✅ Final fixed version of script.lua with proper nil checks

local function safe_require(module_name)
    local ok, value = pcall(require, module_name)
    if not ok then
        ac.log(module_name .. " was not found!")
        return nil
    end
    return value
end

local sim_turbo_ref_model = safe_require("script_sim_turbo_ref_model")
local sim_clutch_model = safe_require("script_sim_clutch_model")

function script.update(dt)
    if type(sim_turbo_ref_model) == "table" and sim_turbo_ref_model.runTurboRefModel then
        sim_turbo_ref_model.runTurboRefModel()
    end
    if type(sim_clutch_model) == "table" and sim_clutch_model.runClutchModel then
        sim_clutch_model.runClutchModel()
    end
end
