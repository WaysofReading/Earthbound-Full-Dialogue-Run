-- #########################################
-- #                                       #
-- #  EarthBound Utils Script for BizHawk  #
-- #                                       #
-- #  Author: Ways of Reading              #
-- #                                       #
-- #  Original by pirohiko for Snes9x      #
-- #  https://pastebin.com/z1ueHSZG        #
-- #                                       #
-- #  Further additions by BrunoValads     #
-- #  This version Ways of Reading         #
-- #                                       #
-- #########################################

-- CONFIGURATION --

local Left_gap = 80 -- change these values if the emu doesn't fit in your screen
local Top_gap = 80
local Right_gap = 80
local Bottom_gap = 80

-- MAIN --

local RNG24 = {}
local RNG26 = {}
local RNG   = {}
local bit = 0
local RNGoffset = -70
local RNGend = 14592
local RNGpos = -70
RNG24[RNGoffset] = 4660
RNG26[RNGoffset] = 120
RNG[RNGoffset] = 134
 
for i=RNGoffset+1,RNGend do
  RNG24[i] = math.floor((RNG24[i-1]+bit)/2)+32768*math.fmod(RNG24[i-1]+bit,2)
  RNG26[i] = math.fmod(RNG26[i-1]+109, 256)
  RNG[i] = math.fmod(math.floor(math.fmod(RNG24[i],256)*RNG26[i]/16),256)
  bit = math.fmod(math.floor(math.fmod(RNG24[i],256)*RNG26[i]/4),4)
end
 
function search_RNGpos()
  local cur24 = mainmemory.read_u16_le(0x0024)
  local cur26 = mainmemory.read_u8(0x0026)
  RNGpos = RNGoffset
  for i=RNGoffset, 256 do
    if(RNG26[i]==cur26) then
      for j=i, RNGend, 256 do
        if(RNG24[j]==cur24) then
          RNGpos = j
          break
        end
      end
      break
    end
  end
end
 
function draw_RNGgraph(x,y,width,height) --draw_RNGgraph(0,288,255,32)
  
  local RNG_str = string.format("%5d/%5d", RNGpos, RNGend)
  gui.text(2*256 - 10*string.len(RNG_str) - 2 + 2*Left_gap, 2*224 + 2*Top_gap, RNG_str)
  gui.text(2 + 2*Left_gap, 2*224 + 2*Top_gap, string.format("RNG: %3d", RNG[RNGpos]))
  
  gui.drawBox(x + Left_gap, y-1 + Top_gap, x+width + Left_gap, y+height+1 + Top_gap, 0x50FFFFFF)
  gui.drawLine(x+36 + Left_gap, y+height+2 + Top_gap, x+36 + Left_gap, y-2 + Top_gap, 0xffFFFFFF)
  
  local color
  
  for i=0,width do
    color = 0x8000FF20
    local curRNG = RNG[(RNGpos+i)%14592]
    if curRNG==0 then
      color = 0xffFF1010 -- 1/128 Item Drop
      curRNG=256
    elseif curRNG==128 then
      color = 0xffFFFF30 -- 1/128 Item Drop
    elseif curRNG==255 then
      color = 0xffFF8000 -- MAX
      curRNG=256
    elseif curRNG<=12 then
      color = 0xffFF5050 -- SMAAAASH!!
    elseif curRNG>184 then
      color = 0x900080FF -- No enemies
    end
    gui.drawLine(x+i + Left_gap, y+height + Top_gap, x+i + Left_gap, y+height-math.floor(curRNG/256*height) + Top_gap,color)
  end
  
  x, y = 2*128 + 2*Left_gap - 10*10/2, 2*(y+height) + 2*Top_gap + 4
  color = 0x8000FF20
  gui.text(x, y, "  No use  ", color)
  
  y = y + 14
  color = 0xffFF5050
  gui.text(x, y, "SMAAAASH!!", color)
  
  y = y + 14
  color = 0xff0080FF
  gui.text(x, y, "No enemies", color)
  
  y = y + 14
  color = 0xffFFFF30
  gui.text(x, y, "1/128 Item", color)
end
 
 
function watch_pos()
  
  -- General info
  
  gui.text(2, 2, emu.framecount())
  
  local game_mode = mainmemory.read_u8(0x0015) -- maybe?

  local x, y = 2*128 - 10*15/2 + 2*Left_gap, 2*Top_gap - 28
  local camera_x = mainmemory.read_s16_le(0x0031)
  local camera_y = mainmemory.read_s16_le(0x0033)
  gui.text(x,y, string.format("Camera X: %5d \nCamera Y: %5d", camera_x, camera_y))
  
  if game_mode == 32 then -- map mode
    gui.text(2*(256 + 64 + Left_gap) - 5*10, 2*(-64 + Top_gap), "spawn \n area", 0x80FFFFFF)
    gui.drawBox(-64 + Left_gap, -64 + Top_gap, 256 + 64 + Left_gap, 224 + 64 + Top_gap, 0x80FFFFFF)
  end
  
  --grid
  for i = 0, 15 do
    for j = 0, 13 do
      local x_base = 16*math.floor(camera_x/16)
      local y_base = 16*math.floor(camera_y/16)
      
      local x_origin, y_origin = -camera_x, -camera_y
      -- gui.drawRectangle(x_base - camera_x + i*16 + Left_gap, y_base - camera_y + j*16 + Top_gap, 15, 15, 0xA000FFFF)
    end
  end
  
  -- Player info
  
  x, y = 2, 2*Top_gap
  local ness_hp = mainmemory.read_u16_le(0x9FC1)
  gui.text(x, y,"Ness HP:  "..ness_hp, 0xffFFFF30)

  y = y + 14
  local ness_pp = mainmemory.read_u16_le(0x9FC5)
  gui.text(x, y,"Ness PP:  "..ness_pp, 0xffFFFF30)
  
  y = y + 14
  local m = mainmemory.read_s16_le(0x9831)
  gui.text(x, y, "Money:    "..m)
  
  y = y + 14
  local atm = mainmemory.read_s16_le(0x9835)
  gui.text(x, y, "ATM:      "..atm)
  
  y = y + 14
  local ss = mainmemory.read_s16_le(0x9E3C)
  gui.text(x, y, "Skip S.:  "..ss)
  
  y = y + 14
  local dr = mainmemory.read_s16_le(0xA934)
  gui.text(x, y, "Drop   :  "..dr)
  
  y = y + 28
  local xadr = 0x9875
  gui.text(x,y,
    string.format("X-Pos: %5d \n",mainmemory.read_u16_le(xadr+2))..
    string.format("X-Sub: %5d \n",mainmemory.read_u16_le(xadr-0))..
    string.format("Y-Pos: %5d \n",mainmemory.read_u16_le(xadr+6))..
    string.format("Y-Sub: %5d \n",mainmemory.read_u16_le(xadr+4))
  )
  local x_screen = mainmemory.read_u16_le(xadr+2) - camera_x + Left_gap
  local y_screen = mainmemory.read_u16_le(xadr+6) - camera_y + Top_gap
  gui.drawAxis(x_screen, y_screen, 3, 0xffFF0000)
  
  
  -- Battle info
  
  if game_mode == 16 or game_mode == 6 then -- battle mode
    local enemy_hp_str = string.format("HP: %d", mainmemory.read_u16_le(0xA22F))
    gui.text(2*128 - 10*string.len(enemy_hp_str)/2 + 2*Left_gap, 163 + 2*Top_gap, enemy_hp_str, 0xffFFFF30)
  end
  
  
  -- Sprite info
  
  --[[
  if game_mode == 32 then -- map mode
    for i = 0, 14-1 do -- there are 14 sprite slots, apparently
      local sprite_id = mainmemory.read_u16_le(0x0A62 + 2*i)
      
      if sprite_id ~= 65535 then -- sprite is active
        local sprite_x_pos = mainmemory.read_u16_le(0x0B8E + 2*i)
        local sprite_y_pos = mainmemory.read_u16_le(0x0BCA + 2*i)
        
        local x_screen = sprite_x_pos - camera_x + Left_gap
        local y_screen = sprite_y_pos - camera_y + Top_gap
        
        gui.drawAxis(x_screen, y_screen, 3, 0xffFF0000)
        --gui.drawRectangle(x_screen - 8, y_screen - 24, 16, 32)
        
        local sprite_slot_str = string.format("#%02d", i)
        gui.text(2*x_screen - 10*string.len(sprite_slot_str)/2, 2*y_screen + 14, sprite_slot_str, 0xffFF0000)
        local sprite_id_str = string.format("(%d)", sprite_id)
        gui.text(2*x_screen - 10*string.len(sprite_id_str)/2, 2*y_screen + 28, sprite_id_str, 0xffFF0000)
      end
    end
  end
  ]]
  
  --[[
  enemy 1 x pos: 0x0B8E
  Ness x pos: 0x0BBE
  2nd partner x pos: 0x0BC6
  1st partner x pos: 0x0BC8
  
  enemy 1 y pos: 0x0BCA
  Ness y pos: 0x0BFA
  2nd partner y pos: 0x0C02
  1st partner y pos: 0x0C04
  
  tables are offset by 0x3C bytes (60 bytes, 30 slots)
  ]]
end
 
event.onframestart(search_RNGpos)

client.SetGameExtraPadding(Left_gap, Top_gap, Right_gap, Bottom_gap)

while true do
  draw_RNGgraph(0,238,255,32)
  watch_pos()
  
  emu.frameadvance()
end
