-- #########################################
-- #                                       #
-- #  EarthBound Utils Script for BizHawk  #
-- #                                       #
-- #  Author: BrunoValads                  #
-- #                                       #
-- #  Original by pirohiko for Snes9x      #
-- #  https://pastebin.com/z1ueHSZG        #
-- #                                       #
-- #########################################

-- CONFIGURATION --

local Left_gap = 80
local Top_gap = 68
local Right_gap = 80
local Bottom_gap = 68
-- Suits for 2x screen size. change these values if you want other sizes.

local offset = 0x4E

-- MAIN --
memory.usememorydomain("WRAM")
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
  local cur24 = memory.read_u16_le(0x0024)
  local cur26 = memory.read_u8(0x0026)
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
 
function draw_RNGgraph(x,y,width,height)
  local rng3 = memory.read_u16_le(0x4A7A)
  local RNG_str = string.format("%5d/%5d", RNGpos, RNGend)
  
  gui.drawBox(x + Left_gap, y-1 + Top_gap, x+width + Left_gap, y+height+1 + Top_gap, 0x50FFFFFF)
  gui.drawLine(x+43 + Left_gap, y+height+2 + Top_gap, x+43 + Left_gap, y-2 + Top_gap, 0xffFFFFFF)
  
  local color
  
  for i=0,width do
    color = 0x8000FF20
    local curRNG = RNG[(RNGpos+i)%14592]
    if curRNG==0 then
      color = 0xffFFFF30 -- 1/128 Item Drop
      curRNG=256
    elseif curRNG==128 then
      color = 0xffFFFF30 -- 1/128 Item Drop
    elseif curRNG==255 then
      color = 0xffFF8000 -- MAX
      curRNG=256
    elseif curRNG<=12 then
      color = 0xffFF5050 -- SMAAAASH!!
    elseif curRNG> 184 then
      color = 0x900080FF -- No enemies
    end
    gui.drawLine(x+i + Left_gap, y+height + Top_gap, x+i + Left_gap, y+height-math.floor(curRNG/256*height) + Top_gap,color)
  end
end
 
 
function watch_pos()
  
  gui.text(2, 2, emu.framecount())
  gui.text(2, 16, emu.lagcount(),"red")
  
  local game_mode = memory.read_u8(0x0015) -- maybe?

  local x, y = 2*128 - 10*15/2 + 2*Left_gap, 2*Top_gap - 28
  local camera_x = memory.read_s16_le(0x0031)
  local camera_y = memory.read_s16_le(0x0033)
  local enemy_number = memory.read_u8(0x4A5C,"WRAM")

  -- Sprite info
    
  if game_mode == 32 then -- map mode
    for i=1, 6 do
      local line_x = Left_gap -64 - (camera_x % 0x40) + i*64
      local line_y = Top_gap -64 - (camera_y % 0x40) + i*64
      gui.drawLine(line_x, Top_gap-64, line_x, Top_gap+64+224, 0x80FFFFFF )
      gui.drawLine(Left_gap-64, line_y, Left_gap+64+256, line_y, 0x80FFFFFF )
    end
    for i = 0, 22-1 do -- there are 22 sprite slots
      local sprite_id = memory.read_u16_le(0x0A62 + 2*i)
      local color_table = {
          0xFF0000,0xFF4000,0xFF8000,0xFFC000,
          0xFFFF00,0xC0FF00,0x80FF00,0x40FF00,
          0x00FF00,0x00FF40,0x00FF80,0x00FFC0,
          0x00FFFF,0x00C0FF,0x0080FF,0x0040FF,
          0x0000FF,0x4000FF,0x8000FF,0xC000FF,
          0xFF00FF,0xFF00C0,0xFF0080,0xFF0040
      }
      if sprite_id ~= 65535 then -- sprite is active
        local sprite_x_pos = memory.read_u16_le(0x0B8E + 2*i)
        local sprite_y_pos = memory.read_u16_le(0x0BCA + 2*i)
        
        local x_screen = sprite_x_pos - camera_x + Left_gap
        local y_screen = sprite_y_pos - camera_y + Top_gap
        
        gui.drawAxis(x_screen, y_screen, 3, 0xffFF0000)
        --gui.drawRectangle(x_screen - 8, y_screen - 24, 16, 32)
        local color = color_table[i+1] + 0xff000000
        local sprite_slot_str = string.format("#%02d", i)
        gui.text(2*x_screen - 10*string.len(sprite_slot_str)/2, 2*y_screen + 14, sprite_slot_str, color)
        local sprite_id_str = string.format("(%04X)", sprite_id)
        gui.text(2*x_screen - 10*string.len(sprite_id_str)/2, 2*y_screen + 28, sprite_id_str, color)
        gui.text(Left_gap*2 + 520, Top_gap*2 + i*16, string.format("#%02d:%04X", i, sprite_id), color)
      else
        local color = color_table[i+1] + 0x20000000
        gui.text(Left_gap*2 + 520, Top_gap*2 + i*16, string.format("#%02d:%04X", i, sprite_id), color)
      end
    end
  end

  local rng3 = memory.read_u16_le(0x4A7A)
  local RNG_str = string.format("%5d/%5d", RNGpos, RNGend)
  gui.text(2*256 - 10*string.len(RNG_str) - 2 + 2*Left_gap, 2*224 + 2*Top_gap, RNG_str)
  gui.text(2 + 2*Left_gap, 2*224 + 2*Top_gap, string.format("RNG: %3d   RNG3:%d", RNG[RNGpos],rng3))

  gui.text(x,y-6, string.format("Camera X: %5d \nCamera Y: %5d     Enemy: %d/10", camera_x, camera_y,enemy_number))
  
  if game_mode == 32 then -- map mode
    gui.text(2*(256 + 64 + Left_gap) - 5*10, 2*(-64 + Top_gap), "spawn \n area", 0x80FFFFFF)
    gui.drawBox(-64 + Left_gap, -64 + Top_gap, 256 + 64 + Left_gap, 224 + 64 + Top_gap, 0x80FFFFFF)
  end
  
  -- Player info
  
  x, y = 2, 2*Top_gap
  local ness_hp = memory.read_u16_le(0x9A15)
  gui.text(x, y,"Ness HP: "..ness_hp, 0xffFFFF30)
  
  y = y + 14
  local m = memory.read_s16_le(0x9831)
  gui.text(x, y, "Money  : "..m)
  
  y = y + 14
  local atm = memory.read_s32_le(0x9835)
  gui.text(x, y, "ATM    : "..atm)
  
  y = y + 14
  local ss = memory.read_u16_le(0x9E3C)
  gui.text(x, y, "Skip S.: "..ss)
  
  y = y + 14
  local dr = memory.read_s16_le(0xAA10)
  gui.text(x, y, "Drop   : "..dr)
  
  y = y + 28
  local xadr = 0x9875
  gui.text(x,y,
    string.format("X-Pos: %5d \n",memory.read_u16_le(xadr+2))..
    string.format("X-Sub: %5d \n",memory.read_u16_le(xadr-0))..
    string.format("Y-Pos: %5d \n",memory.read_u16_le(xadr+6))..
    string.format("Y-Sub: %5d \n",memory.read_u16_le(xadr+4))
  )
  local x_screen = memory.read_u16_le(xadr+2) - camera_x + Left_gap
  local y_screen = memory.read_u16_le(xadr+6) - camera_y + Top_gap
  gui.drawAxis(x_screen, y_screen, 3, 0xffFF0000)

  --Another way of showing RNG values for those who are familiar with Snes9x
  local rng1_text = string.format("%4X",memory.read_u16_le(0x0024))
  local rng2_text = string.format("%4X",memory.read_u16_le(0x0026))
  local rng3_text = string.format("%4X",memory.read_u16_le(0x4A7A))
  x, y = 2, 2*Top_gap + 400
  gui.text(x,y,"RNG1: "..rng1_text)

  y = y + 14
  gui.text(x,y,"RNG2: "..rng2_text)

  y = y + 14
  gui.text(x,y,"RNG3: "..rng3_text)
  
  -- Battle info
  
  if game_mode == 16 or game_mode == 6 then -- battle mode
    local enemy_hp_str = string.format("HP: %d", memory.read_u16_le(0xA22F))
    gui.text(2*128 - 10*string.len(enemy_hp_str)/2 + 2*Left_gap, 163 + 2*Top_gap, enemy_hp_str, 0xffFFFF30)
  
    x, y = 2, 2*Top_gap +164
    gui.text(x, y,"Speeds")

    y = y + 14
	  gui.text(x,y,
    string.format("Ness  : %d \n",memory.read_u16_le(0x9FF2))..
    string.format("Paula : %d \n",memory.read_u16_le(0x9FF2+offset))..
    string.format("Jeff  : %d \n",memory.read_u16_le(0x9FF2+offset*2))..
    string.format("Poo   : %d \n",memory.read_u16_le(0x9FF2+offset*3))..
	string.format("-----\n")..
	string.format("Enemy1: %d \n",memory.read_u16_le(0xA262))..
	string.format("Enemy2: %d \n",memory.read_u16_le(0xA262+offset))..
	string.format("Enemy3: %d \n",memory.read_u16_le(0xA262+offset*2))..
	string.format("Enemy4: %d \n",memory.read_u16_le(0xA262+offset*3))..
	string.format("Enemy5: %d \n",memory.read_u16_le(0xA262+offset*4))..
	string.format("Enemy6: %d \n",memory.read_u16_le(0xA262+offset*5))
  )
  end
  
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