console.clear()

-- RNG graph code by pirohiko and BrunoValads
-- Other code by Ways of Reading

local ftcsv = require "ftcsv"

-- FILE PATHS --
local DIALOGUE_TABLE_PATH = ".\\dialogue-table.csv"
local NOTES_TABLE_PATH = ".\\notes-table.csv"
local ROUTE_TABLE_PATH = ".\\route-table.csv"

-- CONSTANTS --
local DIALOGUE_ROM_MIN = 0xc50000
local  DIALOGUE_ROM_MAX = 0xc9ffff
local TEXT_CALL_STACK_START = 0x96c5

-- GLOBALS --
local THIS_FRAME = emu.framecount()

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
		local note = v.text
		return_table[addr] = note
	end
	return return_table
end



function build_bytes_table()
	bt = {}
	for i=DIALOGUE_ROM_MIN, DIALOGUE_ROM_MAX do
		bt[i] = {frames = {}}
	end
	return bt
end


-- REFERENCE TABLES -- 
local DIALOGUE_TABLE = open_dialogue_table()
local NOTES_TABLE = open_notes_table()
local ROUTE_TABLE = ftcsv.parse(ROUTE_TABLE_PATH, ",")
local BYTES_TABLE = build_bytes_table()
local ROUTE_POS = 316
local ROUTE_SCROLL_TIMEOUT = 0
local ROUTE_STEPS_VISIBLE = 8



-- DISPLAY ELEMENTS --
local PALETTE = {
	RED = 0xffE62727,
	YELLOW = 0xffE6BD27,
	GREEN = 0xff27E65D,
	BLUE = 0xff2738E6,
	CYAN = 0xff16E6D9,
	MAGENTA = 0xff8617E6,
	ORANGE = 0xffE65C17,
	WHITE = 0xffF2F2F2,
	GRAY = 0xffBFBFBF,
	BLACK = 0xff0D0D0D
}

local DISPLAY_PAD_LEFT = 160
local DISPLAY_PAD_TOP = 48
local DISPLAY_PAD_RIGHT = 512
local DISPLAY_PAD_BOTTOM = 204

local GAME_RESOLUTION_X = 256
local GAME_RESOLUTION_Y = 224
local INNER_MARGIN = 4
local LINE_SPACING = 7
local COL_SPACING = 10

local SCALE_FACTOR = 2

local INNER_MARGIN = INNER_MARGIN * SCALE_FACTOR
local LINE_SPACING = LINE_SPACING * SCALE_FACTOR
local COL_SPACING = COL_SPACING * SCALE_FACTOR
local GAME_RESOLUTION_X = GAME_RESOLUTION_X * SCALE_FACTOR
local GAME_RESOLUTION_Y = GAME_RESOLUTION_Y * SCALE_FACTOR

local FONT_BODY_SIZE = 12
local FONT_HEADER_1_SIZE = 16

local STEP_TIMEOUT_FRAMES = 16

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

-- Initialize RNG values
for i=RNGoffset+1,RNGend do
	RNG24[i] = math.floor((RNG24[i-1]+bit)/2)+32768*math.fmod(RNG24[i-1]+bit,2)
	RNG26[i] = math.fmod(RNG26[i-1]+109, 256)
	RNG[i] = math.fmod(math.floor(math.fmod(RNG24[i],256)*RNG26[i]/16),256)
	bit = math.fmod(math.floor(math.fmod(RNG24[i],256)*RNG26[i]/4),4)
end

-- Initialize tracked WRAM addresses
local WRAM = {
	HP_NESS_MAX = {address=0x99d8, bytes=2, signed=false, value=0},
	HP_NESS_ACTUAL = {address=0x9a15, bytes=2, signed=false, value=0},
	HP_PAULA_MAX = {address=0x9a37, bytes=2, signed=false, value=0},
	HP_PAULA_ACTUAL = {address=0x9a74, bytes=2, signed=false, value=0},
	HP_JEFF_MAX = {address=0x9a96, bytes=2, signed=false, value=0},
	HP_JEFF_ACTUAL = {address=0x9ad3, bytes=2, signed=false, value=0},
	HP_POO_MAX = {address=0x9af5, bytes=2, signed=false, value=0},
	HP_POO_ACTUAL = {address=0x9b32, bytes=2, signed=false, value=0},
	PP_NESS_MAX = {address=0x99da, bytes=2, signed=false, value=0},
	PP_NESS_ACTUAL = {address=0x9a1b, bytes=2, signed=false, value=0},
	PP_PAULA_MAX = {address=0x9a39, bytes=2, signed=false, value=0},
	PP_PAULA_ACTUAL = {address=0x9a7a, bytes=2, signed=false, value=0},
	PP_JEFF_MAX = {address=0x9a98, bytes=2, signed=false, value=0},
	PP_JEFF_ACTUAL = {address=0x9ad9, bytes=2, signed=false, value=0},
	PP_POO_MAX = {address=0x9af7, bytes=2, signed=false, value=0},
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
	TIMER_DAD = {address=0x9e54, bytes=2, signed=false, value=0},
	RNG_24 = {address=0x0024, bytes=2, signed=false, value=0},
	RNG_26 = {address=0x0026, bytes=1, signed=false, value=0}
}

-- Initialize dialogue history
local DIALOGUE_HISTORY_LINE_LIMIT = 3
local DIALOGUE_HISTORY_SIZE = 64
-- local DIALOGUE_HISTORY_VERBOSITY = "Full"
local DIALOGUE_HISTORY = {}
for i = 1, DIALOGUE_HISTORY_SIZE do
	DIALOGUE_HISTORY[i] = {
		address = 0x0,
		frame = 0,
		color = PALETTE.WHITE,
		lines = {},
		plaintext = ""
	}
end

-- Initialize text call stack and history for each stack position
local TEXT_CALL_STACK_HISTORY_SIZE = 4
local TEXT_CALL_STACK = {}
for i = 0, 9 do
	TEXT_CALL_STACK[i+1] = {
		address = TEXT_CALL_STACK_START + i * 0x1b,
		bytes = 4,
		signed = false,
		history = {},
		value = 0x0,
		color = PALETTE.GRAY
	}
	for j = 0, TEXT_CALL_STACK_HISTORY_SIZE-1 do
		TEXT_CALL_STACK[i+1].history[j+1] = {
			value = 0x0,
			color = PALETTE.GRAY
		}
	end
end

-- Initialize real-time notes
local NOTES_SIZE = 3
local NOTES = {}
for i = 1, NOTES_SIZE do
	NOTES[i] = {
		address = 0x0,
		text = ""
	}
end

local JOYSTICK = joypad.get(1)

-- Initialize full dialogue run stats
local ROUTE_STATS = {
	READ_COUNT = 0,
	BYTE_COUNT = 0,
	LABEL_COUNT = 0,
	ITEM_COUNT = 0,
	PRESENT_COUNT = 0,
	PHOTO_COUNT = 0,
	HINT_COUNT = 0,
	HEADLINE_COUNT = 0,
	LABEL_TOTAL = 0,
	BYTE_TOTAL = 0,
	PRESENT_TOTAL = 174,
	ITEM_TOTAL = 255,
	OBSCURE_TOTAL = 100,
	PHOTO_TOTAL = 32,
	HINT_TOTAL = 65,
	HEADLINE_TOTAL = 93
}
-- Push the specified value to the specified stack table
function push_to_stack(stack, value)
	for i = #stack, 2, -1 do
		stack[i] = stack[i - 1]
	end
	stack[1] = value
end

-- Count the number of elements in a table (sometimes `#` doesn't work?)
function count_elements(t)
	count = 0
	for k,v in pairs(t) do count = count + 1 end
	return count
end

-- Convert a hex number to a string in format "%x" (default = "$%08x")
function tohex(a, pad_length, prefix, pad_char)
	if prefix == nil then prefix = "$" end
	if pad_char == nil then pad_char = "0" end
	if pad_length == nil then pad_length = 8 end
	return string.format(prefix .. "%" .. pad_char .. pad_length .. "x", a)
end

-- Read the specified WRAM table entry with the proper BizHawk LUA function
function read_memory(a)
	local value = 0x0
	if 		a.bytes == 4 and 		a.signed then value = memory.read_s32_le(a.address, "WRAM")
	elseif 	a.bytes == 4 and 	not a.signed then value = memory.read_u32_le(a.address, "WRAM")
	elseif	a.bytes == 2 and 		a.signed then value = memory.read_s16_le(a.address, "WRAM")
	elseif	a.bytes == 2 and 	not a.signed then value = memory.read_u16_le(a.address, "WRAM")
	elseif	a.bytes == 1 and 		a.signed then value = memory.read_s8(a.address, "WRAM")
	elseif	a.bytes == 1 and 	not a.signed then value = memory.read_u8(a.address, "WRAM") end
	return value
end

function search_RNGpos()
	local cur24 = WRAM.RNG_24.value
	local cur26 = WRAM.RNG_26.value
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
	
	local RNG_str = string.format("%-5d/%5d", RNGpos, RNGend)
	gui.text(SCALE_FACTOR * (x), SCALE_FACTOR * (y), "## RNG MONITOR (by pirohiko and BrunoValads)"); y = y + LINE_SPACING * 1.5
	gui.text(SCALE_FACTOR * (x), SCALE_FACTOR * (y - (LINE_SPACING / 4)), RNG_str)
	gui.text(SCALE_FACTOR * (x), SCALE_FACTOR * (y + height - (LINE_SPACING / 4)), string.format("RNG: %3d", RNG[RNGpos]))
	gui.drawBox(x, y, x + width, y + height + 1, 0x50FFFFFF)
	gui.drawLine(x + 36, y + height + 2, x + 36, y - 2, PALETTE.WHITE)
	
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
	
	x = (x * SCALE_FACTOR)
	y = 2 * (y + height) + 14
	
	color = 0x8000FF20; gui.text(x, y, "No use", color); x = x + 110;
	color = 0xffFF5050; gui.text(x, y, "SMAAAASH!!", color); x = x + 150;
	color = 0xff0080FF; gui.text(x, y, "No enemies", color); x = x + 150;
	color = 0xffFFFF30; gui.text(x, y, "1/128 Item", color)
end

-- Count the number of slots in the given character's inventory
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

-- If Y + UDLR is pressed, scroll through route steps (sorted by "step" on "route-table.csv")
function scroll_route_pos(j)
	if not j.Y then return end

	offset = 0
	if     j.Y and j.Right then offset = 1
	elseif j.Y and j.Up then offset = (ROUTE_STEPS_VISIBLE - 1) * -1
	elseif j.Y and j.Left then offset = -1
	elseif j.Y and j.Down then offset = (ROUTE_STEPS_VISIBLE - 1) end

	if offset ~= 0 and (offset + ROUTE_POS <= #ROUTE_TABLE) and (offset + ROUTE_POS >= 1) then
		ROUTE_SCROLL_TIMEOUT = 6
		ROUTE_POS = ROUTE_POS + offset
	end
end

function evaluate_joypad_input()
	JOYSTICK = joypad.get(1)
	local offset = 0
	if ROUTE_SCROLL_TIMEOUT == 0 then
		scroll_route_pos(JOYSTICK)
	else
		ROUTE_SCROLL_TIMEOUT = ROUTE_SCROLL_TIMEOUT - 1
	end
end

function update_wram()
	for k, v in pairs(WRAM) do
		v.value = read_memory(v)
	end
end

-- Split text into lines on \r\n until DIALOGUE_HISTORY_LINE_LIMIT
function text_to_lines(t)
	lines = {}
	i = 1
	for s in t:gmatch("[^\r\n]+") do
		table.insert(lines, s)
	end
	return lines
end

function add_to_dialogue_history(ptr)
	local t = DIALOGUE_TABLE[ptr.value]
	access_instance = {
		address = ptr.value,
		frame = THIS_FRAME,
		color = ptr.color,
		lines = text_to_lines(t.text),
		plaintext = t.text:gsub("\n", "\\n")
	}
	
	for _, v in pairs(DIALOGUE_HISTORY) do
		if access_instance.address == v.address and 
		   (access_instance.frame == v.frame or
		    access_instance.frame == v.frame + 1) then return end
	end
	push_to_stack(DIALOGUE_HISTORY, access_instance)
end

function add_to_notes(ptr)
	for _, v in pairs(NOTES) do
		if v.address == ptr.value then
			break
		end
	end
	local t = NOTES_TABLE[ptr.value]
	local note = {
		address = ptr.value,
		text = t
	}
	push_to_stack(NOTES, note)
end

function evaluate_dialogue_address(a)
	local dialogue = DIALOGUE_TABLE[a]
	local note = NOTES_TABLE[a]
	r = {
		color = PALETTE.RED,
		value = a
	}

	if a >= DIALOGUE_ROM_MIN and a <= DIALOGUE_ROM_MAX then
		if next(BYTES_TABLE[a].frames) == nil then
			ROUTE_STATS.BYTE_COUNT = ROUTE_STATS.BYTE_COUNT + 1
		end
		table.insert(BYTES_TABLE[a].frames, THIS_FRAME)
		r.color = PALETTE.YELLOW
	end

	if dialogue ~= nil then
		r.color = PALETTE.GREEN
		if dialogue.times_accessed == 0 then
			r.color = PALETTE.CYAN
			ROUTE_STATS.LABEL_COUNT = ROUTE_STATS.LABEL_COUNT + 1
		end
		dialogue.times_accessed = dialogue.times_accessed + 1
		table.insert(dialogue.frames_accessed, THIS_FRAME)
		add_to_dialogue_history(r)
	end
	if note ~= nil then add_to_notes(r)	end
	
end

function set_ptr_color(ptr)
	local dialogue = DIALOGUE_TABLE[ptr.value]
	ptr.color = PALETTE.RED
	if dialogue ~= nil then														ptr.color = PALETTE.GREEN
	elseif ptr.value >= DIALOGUE_ROM_MIN and ptr.value <= DIALOGUE_ROM_MAX then	ptr.color = PALETTE.YELLOW
	else																		ptr.color = PALETTE.RED
	end
end

function check_text_call_stack()
	cursor_value = memory.read_u24_le(emu.getregister("D") + 0x6)
	evaluate_dialogue_address(cursor_value)

	for k, ptr in pairs(TEXT_CALL_STACK) do
		local value_now = read_memory(ptr)
		if value_now ~= ptr.value then
			push_to_stack(ptr.history, {value=ptr.value, color=ptr.color})
			ptr.value = value_now
			set_ptr_color(ptr)
		end
	end

end

function draw_hud_game_stats(x, y)
	local str_template = "%-10s%12s%4s"
	gui.text(x, y, "## GAME STATS"); y = y + LINE_SPACING * 2
	
	gui.text(x, y, string.format(str_template, "Cash", WRAM.INV_CASH.value, "$")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "ATM", WRAM.INV_ATM.value, "$")); y = y + LINE_SPACING * 2

	gui.text(x, y, string.format(str_template, "Map X", WRAM.MAP_PIXEL_X.value, "px")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Map Y", WRAM.MAP_PIXEL_Y.value, "px")); y = y + LINE_SPACING * 2

	local frames = THIS_FRAME
	local time = frames / 60
	local hours = math.floor((time % 86400) / 3600)
	local minutes = math.floor((time % 3600) / 60)
  	local seconds = math.floor((time % 60))
	local timestamp = string.format("%3d:%02d:%02d", hours, minutes, seconds)
	gui.text(x, y, string.format(str_template, "Emu Frame", THIS_FRAME, "#")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Emu Time", timestamp, "hms")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, "Emu Speed", client.get_approx_framerate(), "fps")); y = y + LINE_SPACING
	local chord_str = ""
	for k, v in pairs(JOYSTICK) do
		if v then
			chord_str = chord_str .. string.sub(k, 1, 1)
		else
			chord_str = chord_str .. " "
		end
	end
	gui.text(x, y, string.format(str_template, "Emu Input", chord_str, "t/f")); y = y + LINE_SPACING * 2
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

function draw_hud_route_progress(x, y)
	local r = ROUTE_STATS
	local str_template = "%6d / %6d %-30s"
	gui.text(x, y, "## ROUTE PROGRESS", PALETTE.WHITE); y = y + LINE_SPACING * 2
	local label_ratio = string.format("%.2f", r.LABEL_COUNT / r.LABEL_TOTAL)
	local present_ratio = string.format("%.2f", r.LABEL_COUNT / r.LABEL_TOTAL)
	gui.text(x, y, string.format(str_template, r.BYTE_COUNT, r.BYTE_TOTAL, "Bytes")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, r.LABEL_COUNT, r.LABEL_TOTAL, "Labels")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, r.ITEM_COUNT, r.ITEM_TOTAL, "Items")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, r.PRESENT_COUNT, r.PRESENT_TOTAL, "Presents")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, r.PHOTO_COUNT, r.PHOTO_TOTAL, "Photos")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, r.HINT_COUNT, r.HINT_TOTAL, "Hints")); y = y + LINE_SPACING
	gui.text(x, y, string.format(str_template, r.HEADLINE_COUNT, r.HEADLINE_TOTAL, "Headlines")); y = y + LINE_SPACING
end

function draw_hud_text_call_stack(x, y)
	local str_template = "%4s:%5s"
	gui.text(x, y, "## TEXT CALL STACK", PALETTE.WHITE); y = y + LINE_SPACING * 2

	local row = 0
	local y_start = y
	for k, v in pairs(TEXT_CALL_STACK) do
		if row >= 5 then
			row = 0
			x = x + 120
			y = y_start
		end
		gui.text(x, y, string.format(str_template, tohex(v.address, 4, ""), tohex(v.value, 6, "")), v.color); y = y + LINE_SPACING

		for i, a in ipairs(v.history) do
			local s = tohex(a.value, 6, "")
			gui.text(x, y, string.format(str_template, i*-1, s)); y = y + LINE_SPACING
		end
		y = y + LINE_SPACING
		row = row + 1
	end
end

function draw_hud_dialogue_history(x, y)
	local row_height = LINE_SPACING * (DIALOGUE_HISTORY_LINE_LIMIT + 1)
	local header = "%9s | %7s "
	
	for _, v in pairs(DIALOGUE_HISTORY) do
		local y_top = y - row_height
		if y_top <= (LINE_SPACING * 2) then break end
		gui.text(x, y_top, string.format(header, v.frame, tohex(v.address, 6)))
		x = x + 200
		for _, line in pairs(v.lines) do
			if y_top >= y - LINE_SPACING then break end
			gui.text(x, y_top, line)
			y_top = y_top + LINE_SPACING
		end
		x = x - 200
		y = y - row_height + y - y_top - LINE_SPACING * 2
	end
	y = LINE_SPACING * 2
	gui.text(x, y, string.format(header, "Frame", "Address")); y = y - (LINE_SPACING * 2)
	gui.text(x, y, "## DIALOGUE HISTORY (WIP, SEE COMMENTS)", PALETTE.WHITE)
end

function draw_hud_note(x, y)
	gui.text(x, y, "## RUN NOTES AND ANNOTATIONS")
	y = y + LINE_SPACING * 2

	for k, v in pairs(NOTES) do
		local addr_str = tohex(v.address)
		gui.text (x, y, tohex(v.address, 8, "$", "0"), 0xffFFFF00)
		x = x + 100
		for i = 1, #v.text, 85 do
			gui.text(x, y, string.sub(v.text, i, i + 84))
			y = y + LINE_SPACING
		end; y = y + LINE_SPACING; x = x - 100
		
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
	
	-- Step | action | npc label | npc# | action_class | action_args | action_note | loc
	str_template = "%1s %04d | %-12s | %-16s | #%04d | %-16s | %-24s | %-16s | %-s"
	gui.text(x, y, "## ROUTE NEXT STEPS (Control with Y+UDLR)"); y = y + LINE_SPACING * 2
	
	for i=-2, ROUTE_STEPS_VISIBLE-3 do
		local step = ROUTE_TABLE[ROUTE_POS + i]
		if step == nil then goto continue end
		local caret = ""
		local npc = tonumber(step.npc)
		local step_number = tonumber(step.step)
		local npc_label = string.sub(step.label, 1, 16)
		local action = string.sub(step.action, 1, 12)
		local action_class = ""
		local action_args = ""
		local action_note = ""
		npc = tonumber(step.npc)
		
		if i == 0 then caret = ">" end
		if step.action_class ~= nil then action_class = string.sub(step.action_class, 1, 16) end
		if step.action_args ~= nil then action_args = string.sub(step.action_args, 1, 24) end
		if step.action_note ~= nil then action_note = string.sub(step.action_note, 1, 16) end
		if npc == nil then npc = 9999 end
		
		gui.text(x, y, string.format(str_template,
							caret,
							step_number,
							action,
							npc_label,
							npc,
							action_class,
							action_args,
							action_note,
							string.sub(step.loc, 1, 50))); y = y + LINE_SPACING
	::continue::
	end
end

function initialize()
	event.onmemoryexecute(check_text_call_stack, 0xc187b8)
	client.setwindowsize(SCALE_FACTOR)
	client.SetGameExtraPadding(DISPLAY_PAD_LEFT, DISPLAY_PAD_TOP, DISPLAY_PAD_RIGHT, DISPLAY_PAD_BOTTOM)
	DISPLAY_PAD_LEFT = DISPLAY_PAD_LEFT * SCALE_FACTOR
	DISPLAY_PAD_TOP = DISPLAY_PAD_TOP * SCALE_FACTOR
	DISPLAY_PAD_RIGHT = DISPLAY_PAD_RIGHT * SCALE_FACTOR
	DISPLAY_PAD_BOTTOM = DISPLAY_PAD_BOTTOM * SCALE_FACTOR
	THIS_FRAME = emu.framecount()
	ROUTE_STATS.LABEL_TOTAL = count_elements(DIALOGUE_TABLE)
	ROUTE_STATS.BYTE_TOTAL = count_elements(BYTES_TABLE)
	gui.defaultForeground(PALETTE.WHITE)
	console.clear()
end

function draw_hud_sections()
	
	draw_hud_game_stats(INNER_MARGIN, INNER_MARGIN)
	draw_hud_text_call_stack(INNER_MARGIN, LINE_SPACING*18)
	draw_hud_route_progress(INNER_MARGIN, LINE_SPACING*54)
	
	draw_hud_party_stats(DISPLAY_PAD_LEFT, INNER_MARGIN)
	
	draw_RNGgraph(DISPLAY_PAD_LEFT / 2, (LINE_SPACING*40) / 2, 255, 32)
	draw_hud_route_steps(DISPLAY_PAD_LEFT, LINE_SPACING*54)
	
	draw_hud_dialogue_history(DISPLAY_PAD_LEFT + GAME_RESOLUTION_X + 8, LINE_SPACING*52)
	--draw_hud_note(DISPLAY_PAD_LEFT + GAME_RESOLUTION_X + 8, LINE_SPACING*54)
	
	draw_hud_states(DISPLAY_PAD_LEFT, DISPLAY_PAD_TOP)
end

initialize()
while true do
	gui.cleartext()
	search_RNGpos()
	evaluate_joypad_input()
	update_wram()
	draw_hud_sections()
	emu.frameadvance()
	THIS_FRAME = emu.framecount()
end

