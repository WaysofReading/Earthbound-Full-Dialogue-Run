console.clear()
-- RNG graph code by pirohiko and BrunoValads
-- Other code by Ways of Reading

local ftcsv = require "ftcsv"

-- TRACKING_TABLES --
local DIALOGUE_TABLE_PATH = ".\\dialogue-table.csv"
local NOTES_TABLE_PATH = ".\\notes-table.csv"
local ROUTE_TABLE_PATH = ".\\route-table.csv"

function open_dialogue_table()
	local dialogue_table = ftcsv.parse(DIALOGUE_TABLE_PATH, ",")
	return_table = {}
	for k, v in pairs(dialogue_table) do
		local addr = tonumber(v.address, 16)
		local text = v.dialogue
		return_table[addr] = {text=text, times_accessed=0, frames_accessed={}}
	end
	return return_table
end

function open_notes_table()
	local notes_table = ftcsv.parse(NOTES_TABLE_PATH, ",")
	return_table = {}
	for k, v in pairs(notes_table) do
		local addr = tonumber(v.address, 16)
		local note = v.note
		return_table[addr] = note
	end
	return return_table
end

local DIALOGUE_TABLE = open_dialogue_table()
local NOTES_TABLE = open_notes_table()

local ROUTE_TABLE = ftcsv.parse(ROUTE_TABLE_PATH, ",")
local ROUTE_COUNTER = 1
local ROUTE_COUNTER_SCROLL_TIMEOUT = 0

local ACCESS_HISTORY = {}

-- ROM CONSTANTS --
local DIALOGUE_ROM_MIN = 0xc50000
local  DIALOGUE_ROM_MAX = 0xefa379

-- HUD VALUES --
local DISPLAY_PAD_LEFT = 144
local DISPLAY_PAD_TOP = 48
local DISPLAY_PAD_RIGHT = 512
local DISPLAY_PAD_BOTTOM = 204
local LINE_SPACING = 14
local RECENT_LINE_LIMIT = 8
local SCALE_FACTOR = 2
local ELEMENT_PAD = 4
local FONT_BODY_SIZE = 12
local FONT_HEADER_1_SIZE = 16
local STEP_TIMEOUT_FRAMES = 15
local MAX_POINTER_HISTORY = 8
local MAX_RUN_NOTES = 2

-- RNG Variables --
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

local WRAM = {
	HP_NESS_MAX = {address=0x99d8, bytes=2, signed=false, value=0},
	HP_NESS_ACTUAL = {address=0x9a15, bytes=2, signed=false, value=0},
	HP_NESS_ROLLING = {address=0x9a13, bytes=2, signed=false, value=0},

	HP_PAULA_MAX = {address=0x9a37, bytes=2, signed=false, value=0},
	HP_PAULA_ACTUAL = {address=0x9a74, bytes=2, signed=false, value=0},
	HP_PAULA_ROLLING = {address=0x9a72, bytes=2, signed=false, value=0},
	
	HP_JEFF_MAX = {address=0x9a96, bytes=2, signed=false, value=0},
	HP_JEFF_ACTUAL = {address=0x9ad3, bytes=2, signed=false, value=0},
	HP_JEFF_ROLLING = {address=0x9ad1, bytes=2, signed=false, value=0},
	
	HP_POO_MAX = {address=0x9af5, bytes=2, signed=false, value=0},
	HP_POO_ACTUAL = {address=0x9b32, bytes=2, signed=false, value=0},
	HP_POO_ROLLING = {address=0x9b30, bytes=2, signed=false, value=0},
	
	PP_NESS_MAX = {address=0x99da, bytes=2, signed=false, value=0},
	PP_NESS_ACTUAL = {address=0x9a1b, bytes=2, signed=false, value=0},
	PP_NESS_ROLLING = {address=0x9a19, bytes=2, signed=false, value=0},
	
	PP_PAULA_MAX = {address=0x9a39, bytes=2, signed=false, value=0},
	PP_PAULA_ACTUAL = {address=0x9a7a, bytes=2, signed=false, value=0},
	PP_PAULA_ROLLING = {address=0x9a78, bytes=2, signed=false, value=0},
	
	PP_JEFF_MAX = {address=0x9a98, bytes=2, signed=false, value=0},
	PP_JEFF_ACTUAL = {address=0x9ad9, bytes=2, signed=false, value=0},
	PP_JEFF_ROLLING = {address=0x9ad7, bytes=2, signed=false, value=0},

	PP_POO_MAX = {address=0x9af7, bytes=2, signed=false, value=0},
	PP_POO_ROLLING = {address=0x9b36, bytes=2, signed=false, value=0},
	PP_POO_ACTUAL = {address=0x9b38, bytes=2, signed=false, value=0},

	INV_NESS_LAST = {address=0x99fe, bytes=1, signed=false, value=0},
	INV_PAULA_LAST = {address=0x9a5d, bytes=1, signed=false, value=0},
	INV_JEFF_LAST = {address=0x9abc, bytes=1, signed=false, value=0},
	INV_POO_LAST = {address=0x9b1b, bytes=1, signed=false, value=0},
	
	INV_CASH = {address=0x9831, bytes=4, signed=false, value=0},
	INV_ATM = {address=0x9835, bytes=4, signed=false, value=0},
	
	MAP_PIXEL_X = {address=0x9877, bytes=2, signed=false, value=0},
	MAP_PIXEL_Y = {address=0x987b, bytes=2, signed=false, value=0},
	
	TIMER_SKIP_S = {address=0x9e3c, bytes=2, signed=true, value=0},
	TIMER_DAD = {address=0x9e54, bytes=2, signed=false, value=0}
}

local DIALOGUE_POINTERS = {
	NPC = {
		label = "NPC",
		color = 0xffFF0000,
		in_range = false,
		on_table = false,
		has_note = false,
		new_visit = false,
		note = "",
		text = "",
		history = {},
		address = 0x1ed9,
		bytes = 4,
		signed = false,
		value = 0
	},
	DST = {
		label = "DST",
		color = 0xffFF0000,
		in_range = false,
		on_table = false,
		has_note = false,
		new_visit = false,
		note = "",
		text = "",
		history = {},
		address = 0x1eda,
		bytes = 4,
		signed = false,
		value = 0
	},
	GOTO = {
		label = "Goto",
		color = 0xffFF0000,
		in_range = false,
		on_table = false,
		has_note = false,
		new_visit = false,
		note = "",
		text = "",
		history = {},
		address = 0x97ba,
		bytes = 4,
		signed = false,
		value = 0
	}--[[,
	CURSOR = {
		label = "Cursor",
		wram = WRAM.DIALOGUE_PTR_CURSOR,
		color = 0xffFF0000,
		in_range = false,
		on_table = false,
		has_note = false,
		new_visit = false,
		note = "",
		text = "",
		address_now = 0x0,
		address_last_1 = 0x0,
		address_last_2 = 0x0,
		address_last_3 = 0x0,
		address = 0x9c65,
		bytes = 4,
		signed = false,
		value = 0
	}]]--
}

local HUD_VARS = {
	LABELS_ACCESSED_ANY = 0,
	LABELS_ACCESSED_UNIQUE = 0,
	LABELS_TOTAL = 0,
	NOTES = {}
}

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
 
function draw_RNGgraph(x, y, width, height) --draw_RNGgraph(0,288,255,32)
  
  local RNG_str = string.format("%5d/%5d", RNGpos, RNGend)
  gui.text(SCALE_FACTOR * (x), SCALE_FACTOR * (y), "## RNG MONITOR (by pirohiko and BrunoValads)"); y = y + LINE_SPACING * 1
  gui.text(SCALE_FACTOR * (x), SCALE_FACTOR * (y - 6), RNG_str)
  gui.text(SCALE_FACTOR * (x), SCALE_FACTOR * (y + height), string.format("RNG: %3d", RNG[RNGpos]))
  
  gui.drawBox(x, y, x + width, y + height + 1, 0x50FFFFFF)
  gui.drawLine(x + 36, y + height + 2, x + 36, y - 2, 0xffFFFFFF)
  
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
    gui.drawLine(x + i, y + height, x + i, y + height -math.floor(curRNG/256*height), color)
  end
  
  x = x * SCALE_FACTOR
  y = 2 * (y + height) + 14
  color = 0x8000FF20
  gui.text(x, y, "No use", color); x = x + 110;
  
  color = 0xffFF5050
  gui.text(x, y, "SMAAAASH!!", color); x = x + 150;
  
  color = 0xff0080FF
  gui.text(x, y, "No enemies", color); x = x + 150;
  
  color = 0xffFFFF30
  gui.text(x, y, "1/128 Item", color)
end

function count_free_slots(character_name)
	last_slot_address = WRAM["INV_" .. character_name .. "_LAST"]["address"]
	local free_slots = 0
	for i=0,14 do
		in_slot = mainmemory.read_u8(last_slot_address - i)
		if in_slot == 0 then
			free_slots = free_slots + 1
		else
			break
		end
	end
	return free_slots
end

function count_elements(t)
	count = 0
	for k,v in pairs(t) do count = count + 1 end
	return count
end

function bitand(a, b)
	-- https://stackoverflow.com/a/32387452
    local result = 0
    local bitval = 1
    while a > 0 and b > 0 do
      if a % 2 == 1 and b % 2 == 1 then -- test the rightmost bits
          result = result + bitval      -- set the current bit
      end
      bitval = bitval * 2 -- shift left
      a = math.floor(a/2) -- shift right
      b = math.floor(b/2)
    end
    return result
end

function tohex(a)
	return string.format("$%x", a)
end

function read_memory(a)
	local value = 0x0
	if 		a.bytes == 4 and 		a.signed then value = mainmemory.read_s32_le(a.address)
	elseif 	a.bytes == 4 and 	not a.signed then value = mainmemory.read_u32_le(a.address)
	elseif	a.bytes == 2 and 		a.signed then value = mainmemory.read_s16_le(a.address)
	elseif	a.bytes == 2 and 	not a.signed then value = mainmemory.read_u16_le(a.address)
	elseif	a.bytes == 1 and 		a.signed then value = mainmemory.read_s8(a.address)
	elseif	a.bytes == 1 and 	not a.signed then value = mainmemory.read_u8(a.address) end
	return value
end

function apply_joypad_input()
	local j = joypad.get(1)
	local offset = 0
	if ROUTE_COUNTER_SCROLL_TIMEOUT == 0 then
		if not j.Y then return end
		if     j.Y and j.Right then offset = 1
		elseif j.Y and j.Up then offset = 10
		elseif j.Y and j.Left then offset = -1
		elseif j.Y and j.Down then offset = -10 end

		if offset ~= 0 and (offset + ROUTE_COUNTER <= #ROUTE_TABLE) and (offset + ROUTE_COUNTER >= 1) then
			ROUTE_COUNTER_SCROLL_TIMEOUT = 6
			ROUTE_COUNTER = ROUTE_COUNTER + offset
		end
	else
		ROUTE_COUNTER_SCROLL_TIMEOUT = ROUTE_COUNTER_SCROLL_TIMEOUT - 1
	end
end

function update_wram()
	for k, v in pairs(WRAM) do
		v.value = read_memory(v)
	end
end

function get_dialogue_lines(address)
	local all_lines = string.gmatch(DIALOGUE_TABLE[address].text, "[^\r\n]+")
	local selected_lines = {}
	local i = 0
	for line in all_lines do
		if i >= RECENT_LINE_LIMIT then break end
		i = i + 1
		table.insert(selected_lines, line)
	end
	return selected_lines
end

function push_pointer_history(ptr)
	for i = MAX_POINTER_HISTORY, 2, -1 do
		ptr.history[i] = ptr.history[i-1]
	end
	ptr.history[1] = ptr.value
end

function push_note(addr)
	if addr == HUD_VARS.NOTES[1].address then return end
	for i = MAX_RUN_NOTES, 2, -1 do
		HUD_VARS.NOTES[i] = HUD_VARS.NOTES[i - 1]
	end
	HUD_VARS.NOTES[1] = {address=addr, note=NOTES_TABLE[addr]}
end

function update_dialogue_pointers()
	for k, v in pairs(DIALOGUE_POINTERS) do
		evaluate_dialogue_pointer(v)
	end
end

function evaluate_dialogue_pointer(ptr)
	--[[
		This function will change as my understanding of the text parser
		improves. For now it has issues with successive hits to the same reference
		(an issue for the Goto pointer). Because SNES9x core doesn't support
		events on memory read, I need to do my best to manually "deduplicate"
		such references.
	]]--

	-- Dialogue addresses are 3 bytes long
	local address_now = bitand(read_memory(ptr), 0x00FFFFFF)
	local in_range = address_now >= DIALOGUE_ROM_MIN and address_now <= DIALOGUE_ROM_MAX

	if address_now == ptr.value or not in_range then return end
	
	push_pointer_history(ptr)
	ptr.value = address_now
	ptr.in_range = in_range
	ptr.on_table = DIALOGUE_TABLE[address_now] ~= nil
	ptr.has_note = NOTES_TABLE[address_now] ~= nil
	ptr.new_visit = ptr.on_table and DIALOGUE_TABLE[address_now].times_accessed == 0

	if ptr.in_range then ptr.color = 0xffFFFF00	else ptr.color = 0xffFF0000	end

	if ptr.has_note then
		ptr.note = NOTES_TABLE[address_now]
		push_note(address_now)
	else
		ptr.note = ""
	end
	if ptr.on_table then
		table.insert(DIALOGUE_TABLE[address_now].frames_accessed, emu.framecount())
		DIALOGUE_TABLE[address_now].times_accessed = DIALOGUE_TABLE[address_now].times_accessed + 1
		HUD_VARS.LABELS_ACCESSED_ANY = HUD_VARS.LABELS_ACCESSED_ANY + 1
		
		if ptr.new_visit then
			HUD_VARS.LABELS_ACCESSED_UNIQUE = HUD_VARS.LABELS_ACCESSED_UNIQUE + 1
			ptr.color = 0xff00FFFF
		else
			ptr.color = 0xff00FF00
		end

		ptr.text = DIALOGUE_TABLE[address_now].text

		local access_instance = {
			address = address_now,
			frame = emu.framecount(),
			has_note = ptr.has_note,
			ptr_type = ptr.label,
			color = ptr.color,
			line_sample = get_dialogue_lines(address_now)
		}
		table.insert(ACCESS_HISTORY, access_instance)
	else
		ptr.text = ""
	end	
end

function draw_hud_game_stats(x, y)
	local str_template = "%-10s%9s%4s"
	gui.text(x, y, "## GAME STATS"); y = y + LINE_SPACING * 2
	
	gui.text(x, y, string.format(str_template, "Cash", WRAM.INV_CASH.value, "$")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "ATM", WRAM.INV_ATM.value, "$")); y = y + LINE_SPACING * 2

	gui.text(x, y, string.format(str_template, "Map X", WRAM.MAP_PIXEL_X.value, "px")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Map Y", WRAM.MAP_PIXEL_Y.value, "px")); y = y + LINE_SPACING * 2

	local frames = emu.framecount()
	local time = frames / 60
	local hours = math.floor((time % 86400) / 3600)
	local minutes = math.floor((time % 3600) / 60)
  	local seconds = math.floor((time % 60))
	local timestamp = string.format("%3d:%02d:%02d", hours, minutes, seconds)
	gui.text(x, y, string.format(str_template, "Emu Frame", emu.framecount(), "#")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Emu Time", timestamp, "hms")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Emu Speed", client.get_approx_framerate(), "fps")); y = y + LINE_SPACING * 2

	gui.text(x, y, string.format(str_template, "SS Timer", WRAM.TIMER_SKIP_S.value, "ms")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Dad Timer", WRAM.TIMER_DAD.value, "5s"))
end

function draw_hud_party_stats(x, y)
	local str_template = "%-8s%10s%10s%10s%10s"
	-- gui.text(x, y, "                == Party State =="); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "## PARTY", "Ness", "Paula", "Jeff", "Poo")); y = y + LINE_SPACING

	local ness_hp = string.format("%3d/%3d", WRAM.HP_NESS_ACTUAL.value, WRAM.HP_NESS_MAX.value)
	local paula_hp = string.format("%3d/%3d", WRAM.HP_PAULA_ACTUAL.value, WRAM.HP_PAULA_MAX.value)
	local jeff_hp = string.format("%3d/%3d", WRAM.HP_JEFF_ACTUAL.value, WRAM.HP_JEFF_MAX.value)
	local poo_hp = string.format("%3d/%3d", WRAM.HP_POO_ACTUAL.value, WRAM.HP_POO_MAX.value)
	gui.text(x, y, string.format(str_template, "HP", ness_hp, paula_hp, jeff_hp, poo_hp)); y = y + LINE_SPACING

	local ness_pp = string.format("%3d/%3d", WRAM.PP_NESS_ACTUAL.value, WRAM.PP_NESS_MAX.value)
	local paula_pp = string.format("%3d/%3d", WRAM.PP_PAULA_ACTUAL.value, WRAM.PP_PAULA_MAX.value)
	local jeff_pp = string.format("%3d/%3d", WRAM.PP_JEFF_ACTUAL.value, WRAM.PP_JEFF_MAX.value)
	local poo_pp = string.format("%3d/%3d", WRAM.PP_POO_ACTUAL.value, WRAM.PP_POO_MAX.value)
	gui.text(x, y, string.format(str_template, "PP", ness_pp, paula_pp, jeff_pp, poo_pp)); y = y + LINE_SPACING

	local ness_slots = string.format(" %3d/%3d", count_free_slots("NESS"), 14)
	local paula_slots = string.format(" %3d/%3d", count_free_slots("PAULA"), 14)
	local jeff_slots = string.format(" %3d/%3d", count_free_slots("JEFF"), 14)
	local poo_slots = string.format(" %3d/%3d", count_free_slots("POO"), 14)
	gui.text(x, y, string.format(str_template, "Slots", ness_slots, paula_slots, jeff_slots, poo_slots)); y = y + LINE_SPACING

	gui.text(x, y, string.format(str_template, "Malus", "TODO", "TODO", "TODO", "TODO"))
end

function draw_hud_run_progress(x, y)
	local h = HUD_VARS
	local str_template = "%4d / %4d %-30s"
	gui.text(x, y, "## RUN PROGRESS", 0xffFFFFFF); y = y + LINE_SPACING * 2
	-- local label_ratio = string.format("%.2f", h.LABELS_ACCESSED_UNIQUE / h.LABELS_TOTAL)
	-- local present_ratio = string.format("%.2f", h.LABELS_ACCESSED_UNIQUE / h.LABELS_TOTAL)
	gui.text(x, y, string.format(str_template, h.LABELS_ACCESSED_UNIQUE, h.LABELS_TOTAL, "Labels")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, 0, 174, "Presents")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, 0, 255, "Items")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, 0, 100, "Obscure")); y = y + LINE_SPACING
end

function draw_hud_dialogue_pointers(x, y)
	local str_template_head = "%6s %7s %5s"
	gui.text(x, y, "## DIALOGUE POINTERS", 0xffFFFFFF); y = y + LINE_SPACING * 2
	gui.text(x, y, string.format(str_template_head, "Type", "Address", "Note?")); y = y + LINE_SPACING

	for k, v in pairs(DIALOGUE_POINTERS) do
		local note_flag = ""
		if v.has_note then note_flag = " *** " end
		local now = string.format("$%06x", v.value)
		gui.text(x, y, string.format(str_template_head, v.label, now, note_flag), v.color); y = y + LINE_SPACING

		local str_template_hist = "%6s %7s"
		for i, a in ipairs(v.history) do
			local s = ""
			if a ~= nil then local s = string.format("$%06x", a) end
			gui.text(x, y, string.format(str_template_hist, i*-1, string.format("$%06x", a))); y = y + LINE_SPACING
		end
	end
end

function draw_hud_dialogue_history(x, y)
	local str_template = "%9s %4s %7s %5s"
	gui.text(x, y, "## DIALOGUE HISTORY (WIP, SEE COMMENTS)", 0xffFFFFFF); y = y + LINE_SPACING * 2
	gui.text(x, y, string.format(str_template, "Frame", "Type", "Address", "Note?")); y = y + LINE_SPACING + 2
	
	local i = 0
	while y <= SCALE_FACTOR * (DISPLAY_PAD_TOP + ELEMENT_PAD + 268) do
		local a = ACCESS_HISTORY[#ACCESS_HISTORY - i]
		if a ~= nil then
			c = ""
			if a.has_note then c = " *** " end
			gui.text(x, y, string.format(str_template, a.frame, a.ptr_type, string.format("$%6x", a.address), c), a.color); y = y + LINE_SPACING
			x = x + 10
			for _, line in ipairs(a.line_sample) do
				gui.text(x, y, line, 0xffBBBBBB); y = y + LINE_SPACING
			end
			x = x - 10
			y = y + LINE_SPACING
		else
			break
		end
		i = i + 1
	end
end

function draw_hud_note(x, y)
	gui.text(x, y, "## RUN NOTES AND ANNOTATIONS")
	y = y + LINE_SPACING * 2

	for _, note in ipairs(HUD_VARS.NOTES) do
		local addr_str = string.format("$%06x ", note.address)
		local full_text = addr_str .. note.note
		local y_init = y
		for i = 1, #full_text, 70 do
			gui.text(x, y, string.sub(full_text, i, i + 69))
			y = y + LINE_SPACING
		end; y = y + LINE_SPACING
		gui.text (x, y_init, string.format("$%06x ", note.address), 0xffFFFF00)
	end
end

function draw_hud_states(x, y)
	local str_template = "%-6s"
	local paused = client.ispaused()
	local muted = not(client.GetSoundOn())
	if client.ispaused() then
		gui.text(x, y, string.format(str_template, "Paused"), 0xA0FF6347)
	end
	x = x + 70

	if not(client.GetSoundOn()) then
		gui.text(x, y, string.format(str_template, "Muted"), 0xA087CEFA)
	end
	y = y + LINE_SPACING
end

function draw_hud_route_steps(x, y)
	step = ROUTE_TABLE[ROUTE_COUNTER]
	gui.text(x, y, "## ROUTE NEXT STEPS (Control with Y+UDLR)"); y = y + LINE_SPACING * 2
	gui.text(x, y, "Step " .. string.format("%04d", step["Sort Order"]) .. " " .. step.action .. "@" .. step.npc .. "(" .. step.label .. ")"); y = y + LINE_SPACING
	gui.text(x, y, "Details  " .. step.action_class .. "->" .. step.action_args .. "(" .. step.action_note .. ")"); y = y + LINE_SPACING
	gui.text(x, y, "Location " .. step.loc); y = y + LINE_SPACING
	gui.text(x, y, "Placeholder") y = y + LINE_SPACING * 2

	step = ROUTE_TABLE[ROUTE_COUNTER + 1]
	gui.text(x, y, "Step " .. string.format("%04d", step["Sort Order"]) .. " " .. step.action .. "@" .. step.npc .. "(" .. step.label .. ")"); y = y + LINE_SPACING
	gui.text(x, y, "Details  " .. step.action_class .. "->" .. step.action_args .. "(" .. step.action_note .. ")"); y = y + LINE_SPACING
	gui.text(x, y, "Location " .. step.loc); y = y + LINE_SPACING
	gui.text(x, y, "Placeholder"); y = y + LINE_SPACING * 2

	step = ROUTE_TABLE[ROUTE_COUNTER + 2]
	gui.text(x, y, "Step " .. string.format("%04d", step["Sort Order"]) .. " " .. step.action .. "@" .. step.npc .. "(" .. step.label .. ")"); y = y + LINE_SPACING
	gui.text(x, y, "Details  " .. step.action_class .. "->" .. step.action_args .. "(" .. step.action_note .. ")"); y = y + LINE_SPACING
	gui.text(x, y, "Location " .. step.loc); y = y + LINE_SPACING
	gui.text(x, y, "Placeholder")	
end


function initialize()
	HUD_VARS.LABELS_TOTAL = count_elements(DIALOGUE_TABLE)
	for k, v in pairs(DIALOGUE_POINTERS) do
		for i=1, MAX_POINTER_HISTORY do
			v.history[i] = 0
		end
	end

	for i = 1, MAX_RUN_NOTES do
		HUD_VARS.NOTES[i] = {address = 0x0, note = ""}
	end

	client.setwindowsize(SCALE_FACTOR)
	client.SetGameExtraPadding(DISPLAY_PAD_LEFT, DISPLAY_PAD_TOP, DISPLAY_PAD_RIGHT, DISPLAY_PAD_BOTTOM)
	console.clear()
end

function draw_hud_sections()
	
	draw_hud_game_stats(SCALE_FACTOR * (4 + ELEMENT_PAD), SCALE_FACTOR * (ELEMENT_PAD))
	draw_hud_dialogue_pointers(SCALE_FACTOR * (4 + ELEMENT_PAD), SCALE_FACTOR * (ELEMENT_PAD + 105))
	draw_hud_run_progress(SCALE_FACTOR * (4 + ELEMENT_PAD), SCALE_FACTOR * (ELEMENT_PAD + 386))

	draw_hud_party_stats(SCALE_FACTOR * (DISPLAY_PAD_LEFT + ELEMENT_PAD), SCALE_FACTOR * (ELEMENT_PAD))
	draw_hud_states(SCALE_FACTOR * (DISPLAY_PAD_LEFT), SCALE_FACTOR * (DISPLAY_PAD_TOP))

	draw_hud_route_steps(SCALE_FACTOR * (DISPLAY_PAD_LEFT + ELEMENT_PAD), SCALE_FACTOR * (ELEMENT_PAD + DISPLAY_PAD_TOP + 224))
	
	draw_RNGgraph(ELEMENT_PAD + DISPLAY_PAD_LEFT, ELEMENT_PAD + DISPLAY_PAD_TOP + 350,255,32)
		
	draw_hud_dialogue_history(SCALE_FACTOR * (DISPLAY_PAD_LEFT + ELEMENT_PAD + 256 + 8), SCALE_FACTOR * (ELEMENT_PAD))
	draw_hud_note(SCALE_FACTOR * (DISPLAY_PAD_LEFT + ELEMENT_PAD + 256 + 8), SCALE_FACTOR * (ELEMENT_PAD + 386))

	


end

initialize()
while true do
	gui.cleartext()
	search_RNGpos()
	update_wram()
	apply_joypad_input()
	update_dialogue_pointers()
	draw_hud_sections()
	emu.frameadvance()
end
