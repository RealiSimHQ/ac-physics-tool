-- script_dccd.lua — final working version using car:setGripExtra

if car.isAIControlled then return nil end

local counter = 0
local prev_extraB = car.extraB
local prev_extraC = car.extraC
local countertime = 0
local dccd_ratio = 0.0

local function updateDCCDLock()
    dccd_ratio = counter / 5.0
    car:setGripExtra(0, dccd_ratio)  -- ✅ This actually works
end

local function rundccd(dt)
    if car.extraC ~= prev_extraC then
        counter = counter + 1
        prev_extraC = car.extraC
        countertime = 0
        updateDCCDLock()
    end

    if car.extraB ~= prev_extraB then
        counter = counter - 1
        prev_extraB = car.extraB
        countertime = 0
        updateDCCDLock()
    end

    if counter >= 6 then counter = 5 end
    if counter <= -1 then counter = 0 end

    if countertime <= 0.5 then
        countertime = countertime + dt
        local states = { "Open", "1", "2", "3", "4", "Lock" }
        ac.setMessage("DCCD", states[counter + 1])
    end
end

return {
    rundccd = rundccd
}