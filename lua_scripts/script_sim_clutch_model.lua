
local data = ac.accessCarPhysics()
local engine_ini = ac.INIConfig.carData(0, "engine.ini")

local redline = engine_ini:get("ENGINE_DATA", "LIMITER", 10000)
local idle_RPM = engine_ini:get("ENGINE_DATA", "MINIMUM", 1000)
local coast_RPM = engine_ini:get("COAST_REF", "RPM", 10000)
local coast_torque_ref = engine_ini:get("COAST_REF", "TORQUE", 80)
local power_lut = engine_ini:get("HEADER", "POWER_CURVE", "")

local WOT_TORQUE = ac.DataLUT11.carData(0, power_lut)
local gamma = engine_ini:get("THROTTLE_LUA", "THROTTLE_GAMMA", 1.0)
local slope = engine_ini:get("THROTTLE_LUA", "THROTTLE_SLOPE", 1.5)
local throttle_type = engine_ini:get("THROTTLE_LUA", "THROTTLE_TYPE", 0)
local new_idle = engine_ini:get("THROTTLE_LUA", "IDLE_RPM", idle_RPM)

local isIdleInitialized = false
local coast_torque, idle_torque, idle_throttle_ref
local idle_model_throttle, modelled_throttle, final_throttle
local idleCalculated = false
local idle = 0
local idleSpeed = 0
local idleTimer = os.clock()
local gasInput, clutchInput = 0, 0
local engineTimer = os.clock()
local engineTimerBool = false
local engineIntialRPM, engineAfterRPM, engineRPMComparison = 0, 0, 0
local transmissionRpm, relativeRpm, loadTorque = 0, 0, 0

local function _idleModelSetup()
    coast_torque = -(coast_torque_ref / (coast_RPM - idle_RPM)) * (new_idle - idle_RPM)
    idle_torque = WOT_TORQUE:get(new_idle)
    idle_throttle_ref = (0 - coast_torque) / (idle_torque - coast_torque)
    isIdleInitialized = true
end

local function calculateIdleTorque(rpm)
    if data.rpm > 0 then
        return math.saturate(math.min(idle_throttle_ref * new_idle / rpm, idle_throttle_ref * (1 + idle_throttle_ref)))
    else
        return idle_throttle_ref * (1 + idle_throttle_ref)
    end
end

local function calculateTorque(throttle, rpm)
    return ((2 / (1 + math.exp(-((redline / rpm)^gamma * slope * throttle))) - 1)) /
           ((2 / (1 + math.exp(-((redline / rpm)^gamma * slope * 1))) - 1))
end

local function CalculateIdleRPM()
    if idleTimer + 10 > os.clock() then
        ac.setMessage("🔄 Determining Idle RPM...", idle)
        data.gas = 0
        data.requestedGearIndex = 1
        idle = data.rpm
    else
        idleCalculated = true
        throttleLocked = false
        idleTimer = os.clock()
        ac.setMessage("✅ Idle Set: " .. idle, 3)
    end
end

local function ClutchPhysicsSimulation()
    local car = ac.getCar(0)
    local carInfo = ac.getCarPhysics()
    local dataWheelLF = car.wheels[1]

    transmissionRpm = (car.drivetrainSpeed / 1.25 * carInfo.gearRatio * carInfo.finalRatio * 336) / dataWheelLF.tyreRadius / 100
    relativeRpm = transmissionRpm - car.rpm
    idleSpeed = dataWheelLF.tyreRadius * idle * carInfo.gearRatios[2] * carInfo.finalRatio * 0.002

    if relativeRpm > 0 or data.clutch > 0.98 or data.clutch < 0.02 then
        loadTorque = 0
    else
        loadTorque = -relativeRpm * 0.4 * carInfo.clutchState
        if loadTorque > 0 then
            if car.speedKmh < 2 and data.gas < 0.03 and carInfo.gearRatio ~= 0 then
                data.gas = data.gas + 0.02
            end
            if car.drivetrainSpeed < idleSpeed and data.rpm < 2500 then
                ac.addForce(vec3(0, 0, -2), true, vec3(0, 0, loadTorque * 45), true)
            end
        end
    end

    if data.clutch < 0.04 and carInfo.gearRatio ~= 0 then
        data.clutch = 0.03
    end

    if car.speedKmh < 1.5 and data.brake < 0.02 and data.clutch < 0.03 and carInfo.gearRatio ~= 0 then
        data.clutch = data.clutch + 0.02
        data.gas = data.gas + 0.02
    end

    if engineTimer + 0.05 < os.clock() then
        engineTimer = os.clock()
        engineIntialRPM = car.rpm
        if engineRPMComparison > 200 and car.rpm < idle + 200 then
            ac.setEngineRPM(car.rpm - 500)
        end
        engineTimerBool = true
    elseif engineTimerBool then
        engineAfterRPM = car.rpm
        if engineRPMComparison > 200 and car.rpm < idle + 200 then
            ac.setEngineRPM(car.rpm + 150)
        end
        engineTimerBool = false
    end

    if engineIntialRPM - engineAfterRPM > 0 then
        engineRPMComparison = engineIntialRPM - engineAfterRPM
    elseif engineAfterRPM - engineIntialRPM > 0 then
        engineRPMComparison = engineAfterRPM - engineIntialRPM
    end

    if car.rpm < idle - 250 and carInfo.gearRatio ~= 0 then
        ac.setEngineRPM(0)
        ac.setEngineStalling(true)
    end

    if carInfo.gearRatio == 0 and car.rpm < 100 then
        ac.setEngineStalling(false)
        ac.setEngineRPM(idle + 250)
        data.gas = 1
    end
end

local sim_clutch_model = {}
function sim_clutch_model.runClutchModel()
    if not isIdleInitialized then _idleModelSetup() end
    if not idleCalculated then
        CalculateIdleRPM()
        ac.overrideGasInput(0)
    else
        idle_model_throttle = calculateIdleTorque(data.rpm)
        modelled_throttle = calculateTorque(data.gas, data.rpm)
        final_throttle = math.max(modelled_throttle, idle_model_throttle)
        ac.overrideGasInput(final_throttle)
        ClutchPhysicsSimulation()
    end
end

return sim_clutch_model
