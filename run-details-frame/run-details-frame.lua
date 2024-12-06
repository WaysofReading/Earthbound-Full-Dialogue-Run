console.clear()

-- Code by Ways of Reading

local ftcsv = require "ftcsv"

-- FILE PATHS --
local LABELS_PATH = ".\\labels.csv"
local ENTITIES_PATH = ".\\entities.csv"
local HINTS_PATH = ".\\hints.csv"
local ITEM_DESCRIPTIONS_PATH = ".\\item-descriptions.csv"
local HEADLINES_PATH = ".\\headlines.csv"
local SECTIONS_PATH = ".\\sections.csv"

local RECORDING_STATS_FRAME_PATH = ".\\recording-stats-frame.png"

-- RAM ADDRESSES --
local DIALOGUE_ROM_MIN = 0xc50000
local DIALOGUE_ROM_MAX = 0xc9ffff
local TEXT_CALL_STACK_START = 0x96c5
local PRESENT_FLAGS_START = 0x9c6b -- https://datacrystal.tcrf.net/wiki/EarthBound/Flags#Item_box_flags
local PRESENT_FLAGS_END = 0x9c81 -- from 9c6b bit 7 to 9c81 bit 7, each bit corresponds to a present, 0=not opened

-- GLOBALS --
local THIS_FRAME = emu.framecount()
local SECTION_CURRENT = "Intro"
local SECTION_NUMBER = 1

-- DISPLAY VALUES --
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

local DISPLAY_PAD_LEFT = 0
local DISPLAY_PAD_TOP = 160
local DISPLAY_PAD_RIGHT = 800
local DISPLAY_PAD_BOTTOM = 25

-- MATH FUNCTIONS --
function tohex(a, pad_length, prefix, pad_char)
	-- Convert a hex number to a string in format "%x" (default = "$%08x")
	if prefix == nil then prefix = "$" end
	if pad_char == nil then pad_char = "0" end
	if pad_length == nil then pad_length = 8 end
	return string.format(prefix .. "%" .. pad_char .. pad_length .. "x", a)
end

-- STRING FUNCTIONS --
function frames_to_time(frames)
	local hours = math.floor(frames/216000)
	local minutes = math.floor(frames/3600 - (hours*60))
	local seconds = math.floor(frames/60 - (hours*3600) - (minutes*60))
	return string.format("%02i (%02i:%02i:%02.0f)", frames, hours, minutes, seconds)
end

function ratio_and_percent(current, total)
	ratio = (current/total) * 100
	return string.format("%i/%i (%00.1f%%)", current, total, ratio)
end

-- TABLE FUNCTIONS --
function read_csv(csv_path)
	local csv = ftcsv.parse(csv_path, ",")
	return_table = {}
	for k, v in pairs(csv) do
		local addr = tonumber(v.address, 16)
		return_table[addr] = {times_accessed=0, frames_accessed={}}
	end
	return return_table
end

function read_sections_csv(csv_path)
	local csv = ftcsv.parse(csv_path, ",")
	return_table = {}
	for k, v in pairs(csv) do
		local addr = tonumber(v.address, 16)
		return_table[addr] = {label=v.label, order=tonumber(v.order, 10)}
	end
	return return_table
end

function build_bytes_table()
	bt = {}
	for i=0xc50000, 0xc9ffff do
		bt[i] = {times_accessed=0, frames_accessed={}}
	end
	for i=0xef4e20, 0xefa6ff do
		bt[i] = {times_accessed=0, frames_accessed={}}
	end
	return bt
end

function count_all_elements(t)
	count = 0
	for k,v in pairs(t) do
		count = count + 1
	end
	return count
end

-- PROGRESS TRACKING FUNCTIONS --
function evaluate_dialogue_address()
	v = memory.read_u24_le(emu.getregister("D") + 0x6)

	-- Log access on each progress table and update the overall progress counters
	-- (this is a little clumsy but much faster than counting all accessed elements)
	-- (see commented functions below for detail on the previous solution)
	if BYTES_TABLE[v] ~= nil then
		if BYTES_TABLE[v].times_accessed == 0 then
			ROUTE_PROGRESS_TABLE.BYTES_READ = ROUTE_PROGRESS_TABLE.BYTES_READ + 1
		end
		BYTES_TABLE[v].times_accessed = BYTES_TABLE[v].times_accessed + 1
	end

	if LABELS_TABLE[v] ~= nil then
		if LABELS_TABLE[v].times_accessed == 0 then
			ROUTE_PROGRESS_TABLE.LABELS_ACCESSED = ROUTE_PROGRESS_TABLE.LABELS_ACCESSED + 1
		end
		LABELS_TABLE[v].times_accessed = LABELS_TABLE[v].times_accessed + 1
	end

	if ENTITIES_TABLE[v] ~= nil then
		if ENTITIES_TABLE[v].times_accessed == 0 then
			ROUTE_PROGRESS_TABLE.ENTITIES_INTERACTED = ROUTE_PROGRESS_TABLE.ENTITIES_INTERACTED + 1
		end
		ENTITIES_TABLE[v].times_accessed = ENTITIES_TABLE[v].times_accessed + 1
	end

	if HEADLINES_TABLE[v] ~= nil then
		if HEADLINES_TABLE[v].times_accessed == 0 then
			ROUTE_PROGRESS_TABLE.HEADLINES_READ = ROUTE_PROGRESS_TABLE.HEADLINES_READ + 1
		end
		HEADLINES_TABLE[v].times_accessed = HEADLINES_TABLE[v].times_accessed + 1
	end

	if HINTS_TABLE[v] ~= nil then
		if HINTS_TABLE[v].times_accessed == 0 then
			ROUTE_PROGRESS_TABLE.HINTS_SEEN = ROUTE_PROGRESS_TABLE.HINTS_SEEN + 1
		end
		HINTS_TABLE[v].times_accessed = HINTS_TABLE[v].times_accessed + 1
	end

	if ITEM_DESCRIPTIONS_TABLE[v] ~= nil then
		if ITEM_DESCRIPTIONS_TABLE[v].times_accessed == 0 then
			ROUTE_PROGRESS_TABLE.ITEMS_DESCRIBED = ROUTE_PROGRESS_TABLE.ITEMS_DESCRIBED + 1
		end
		ITEM_DESCRIPTIONS_TABLE[v].times_accessed = ITEM_DESCRIPTIONS_TABLE[v].times_accessed + 1
	end

	if SECTIONS_TABLE[v] ~= nil and SECTIONS_TABLE[v].order > SECTION_NUMBER then
		SECTION_CURRENT = SECTIONS_TABLE[v].label
		SECTION_NUMBER = SECTIONS_TABLE[v].order 
	end
end

function count_opened_presents(start_addr, end_addr)
	local presents_opened = 0
	for i=start_addr, end_addr do
		n = memory.read_u8(i, "WRAM")
		for j=7,0,-1 do
    		presents_opened = presents_opened + math.floor(n / 2^j)
    		n = n % 2^j
  		end
	end
	return presents_opened
end

-- DISPLAY FUNCTIONS --
function draw_progress_stats()
	-- box size y = 128px, x = 662px/331px, gap = 32px
	gui.drawString(1240, 190, frames_to_time(THIS_FRAME), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1240, 318, string.format("%02i - %s", SECTION_NUMBER, SECTION_CURRENT), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1240, 478, ratio_and_percent(ROUTE_PROGRESS_TABLE.BYTES_READ, ROUTE_PROGRESS_TABLE.BYTES_TOTAL), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1240, 606, ratio_and_percent(ROUTE_PROGRESS_TABLE.LABELS_ACCESSED, ROUTE_PROGRESS_TABLE.LABELS_TOTAL), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1240, 734, ratio_and_percent(ROUTE_PROGRESS_TABLE.ENTITIES_INTERACTED, ROUTE_PROGRESS_TABLE.ENTITIES_TOTAL), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1240, 862, ratio_and_percent(ROUTE_PROGRESS_TABLE.PRESENTS_OPENED, ROUTE_PROGRESS_TABLE.PRESENTS_TOTAL), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1571, 862, ratio_and_percent(ROUTE_PROGRESS_TABLE.HINTS_SEEN, ROUTE_PROGRESS_TABLE.HINTS_TOTAL), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1240, 990, ratio_and_percent(ROUTE_PROGRESS_TABLE.ITEMS_DESCRIBED, ROUTE_PROGRESS_TABLE.ITEM_DESCRIPTIONS_TOTAL), nil, nil, 36, "Earthbound Dialogue")
	gui.drawString(1571, 990, ratio_and_percent(ROUTE_PROGRESS_TABLE.HEADLINES_READ, ROUTE_PROGRESS_TABLE.HEADLINES_TOTAL), nil, nil, 36, "Earthbound Dialogue")
end

-- Build tables
BYTES_TABLE = build_bytes_table()
LABELS_TABLE = read_csv(LABELS_PATH)
ENTITIES_TABLE = read_csv(ENTITIES_PATH)
HINTS_TABLE = read_csv(HINTS_PATH)
ITEM_DESCRIPTIONS_TABLE = read_csv(ITEM_DESCRIPTIONS_PATH)
HEADLINES_TABLE = read_csv(HEADLINES_PATH)
SECTIONS_TABLE = read_sections_csv(SECTIONS_PATH)

ROUTE_PROGRESS_TABLE = {
	BYTES_READ = 0,
	LABELS_ACCESSED = 0,
	ENTITIES_INTERACTED = 0,
	PRESENTS_OPENED = count_opened_presents(PRESENT_FLAGS_START, PRESENT_FLAGS_END),
	HINTS_SEEN = 0,
	ITEMS_DESCRIBED = 0,
	HEADLINES_READ = 0,
	BYTES_TOTAL = count_all_elements(BYTES_TABLE),
	LABELS_TOTAL = count_all_elements(LABELS_TABLE),
	ENTITIES_TOTAL = count_all_elements(ENTITIES_TABLE),
	PRESENTS_TOTAL = 177,
	HINTS_TOTAL = count_all_elements(HINTS_TABLE),
	ITEM_DESCRIPTIONS_TOTAL = count_all_elements(ITEM_DESCRIPTIONS_TABLE),
	HEADLINES_TOTAL = count_all_elements(HEADLINES_TABLE)
}

function initialize()
	event.onmemoryexecute(evaluate_dialogue_address, 0xc187b8)
	client.SetClientExtraPadding(DISPLAY_PAD_LEFT, DISPLAY_PAD_TOP, DISPLAY_PAD_RIGHT, DISPLAY_PAD_BOTTOM)
	gui.use_surface("client")
	gui.defaultForeground(PALETTE.WHITE)
	gui.drawImage(RECORDING_STATS_FRAME_PATH, 0, 0)
end

initialize()

while true do
	emu.frameadvance()
	THIS_FRAME = emu.framecount()
	if math.fmod(THIS_FRAME, 1) == 0 then
		ROUTE_PROGRESS_TABLE.PRESENTS_OPENED = count_opened_presents(PRESENT_FLAGS_START, PRESENT_FLAGS_END)
		gui.drawImage(RECORDING_STATS_FRAME_PATH, 0, 0)
		draw_progress_stats()
	end
end
