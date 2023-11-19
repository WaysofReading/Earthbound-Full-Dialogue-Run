-- TPP = 0x96C5 -- Text Parser Pointer (expected: 0xC50000 to 0xEFA379)
-- local tpp_last_frame = mainmemory.read_u32_le( TPP );

--[[
local function everyAccess()
	local tpp_now = mainmemory.read_u32_le( TPP );
	print(tpp_now);
end
]]--

-- event.onmemoryread(everyAccess, address=0x96C5, scope="WRAM");

--[[
while true do
	local tpp_this_frame = mainmemory.read_u32_le( 0x96C5 );
	if tpp_this_frame ~= tpp_last_frame then
		print(string.format("dialog pointer: %x", tpp_this_frame));
		-- tpp_last_frame = tpp_this_frame;
	end
	emu.next();
end
]]--

console.clear()
TPP_ADDRESS = 0x96C5 -- Text Parser Pointer (expected: 0xC50000 to 0xEFA379)
TPP_VALUE_NOW = memory.read_u32_le(TPP, "WRAM")
print(string.format("%x", TPP_VALUE_NOW))

while true do
	local TPP_VALUE_NEW = memory.read_u32_le(TPP, "WRAM")
	if TPP_VALUE_NEW ~= TPP_VALUE_NOW then
		TPP_VALUE_NOW = TPP_VALUE_NEW
		print(string.format("%x", TPP_VALUE_NOW))
	end
	emu.frameadvance();
end