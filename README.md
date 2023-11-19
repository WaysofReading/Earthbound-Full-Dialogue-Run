# Earthbound Full Dialogue Run
A full-dialogue run of Earthbound is a playthrough of the game in which every normally-accessible line of overworld and inventory dialogue appears on-screen. “Normally-accessible” means lines of dialogue that are accessible without the use of glitches, cheats, or hacks. Battle-only text such as enemy attacks or in-battle item usage are excluded.

This project repository serves to house and document materials used to develop this complex run.

Note: While I am working on this project as though it were a conventional speedrun, it is also an attempt to explore certain ideas around video game writing, identities, and unconventional play. As such, I am as interested in ways of interpreting this game, run, and route as I am in actually executing it. Additional non-technical discussion can be found in the `docs\` segment of the repository with published posts on at (https://waysofreadingblog.com/tags/earthbound).

## Repository Map

* `resources\` Data, information, and materials
    * `routes\` Materials for the Full Dialogue Run route (the final goal of the project!)
        * `Earthbound Full Dialogue Run - Route.xlsx` The most recent draft of the route
        * `_old\` Old routing files
    * `maps\` Image files and information regarding maps
        * `export-layers_output` Intermediate output (from antipalindrome, `Photoshop-Export-Layers-to-Files-Fast-2.7.1`)
        * `process-images_output` Intermediate output (from `process-images.py`)
            * Filename `06144_06016_06400_06144_Dusty Dunes Desert_Monkey Cave_Start_Left_Left-(Hallway)`
                * x0 (bounding box)
                * x1 (bounding box)
                * y0 (bounding box)
                * y1 (bounding box)
                * Area (English label)
                * SubArea (English label) ...
                * (Note)
                * .png
        * `regions-trimmed-flat` Output from Bulk Rename Utility flattening `process-images_output`
        * `regions-trimmed-flat_by-name` Coordinates removed so list is sortable by name/hierarchy
        * `layers_all-regions-and-rooms.psd` (BIG) all rooms and segmented overworld regions in nested layer structure
        * `layers_overworld-regions-only.psd` Complete overworld regions only in flat layer structure
        * `map-with-npcs_spread_nogrid.png` output from EB Project Editor with NPCs shown (adjusted for visiblity)
    * `recordings\` Emulator and video recordings of full runs and run segments
        * `bk2\` Bizhawk emulator movie files
        * `vid\` Video recordings for sharing and publication
    * `decompilations\` Decompiled data from the Earthbound game ROM
        * `20230106\` A CoilSnake decompilation that is my source for all outputs inventoried here
    * `dialogue\` Text files containing game dialogue in various arrangements
        * `script-dumper_output.txt` Output from Earthbound Script Dumper
        * `script-dumper_output_text-only.txt` Output from Earthbound Script Dumper without CCScript functions
        * `process-dialogue_output.json` Output from process-dialogue.py (uses `script-dumper_output.txt`)
        * `by_npc\` Output from process-dialogue.py, separate text file for each NPC
        * `by_npc_working-set\` Output from process-dialogue.py, free to modify for routing purposes
        * `ccscript_parts\` CCScript files from CoilSnake
        * `flat_dialog.json` Earthbound dialogue processed for ease of reading
    * `tables\` Automatically-generated value lists for game entities
        * `regions-and-rooms.csv` Names and coordinates for all regions and rooms (output from `process-images.py`)
        * `npcs.csv` Detailed table of all NPCs (output from `process-dialogue.py`)
        * `flags.csv` English labels for all numbered game flags (from CataLatas, `earthbound-script-dumper`)
    * `labels\` Manually-created value lists for game entities
        * `sprite-group_labels.csv` English labels for each numbered sprite group
* `utilities\` Scripts, utilities, and tools. Supporting tools created by other authors as annotated below. 
    * `bizhawk\` Technical/TASing/Scripting emulator (https://tasvideos.org/BizHawk)
    * `coilsnake\` Earthbound decompilation and modification tool (https://pk-hack.github.io/CoilSnake/)
    * `earthbound-script-dumper-main\` Tool for refining dumped script (https://github.com/CataLatas/earthbound-script-dumper)
        * `constants\` includes English labels for flags, items, etc.
    * `Photoshop-Export-Layers-to-Files-Fast-2.7.1` Tool to split PSD by layer with options (https://github.com/antipalindrome/Photoshop-Export-Layers-to-Files-Fast)
    * `roms\` This run is based on an unmodified `EarthBound (USA).sfc` (CRC32 = `DC9BB451`)
* `process-images.py` Yields trimmed and renamed versions of images output from `Photoshop-Export-Layers-to-Files-Fast-2.7.1`
* `process-dialogue.py`. Recursively unrolls dumped script, and yields dialogue files and NPC tables

Additional documentation may be available in the Python source code and elsewhere.

## The Run
The run itself is being composed in `routes\Earthbound Full Dialogue Run - Route.xlsx` in this. The sheet includes one row for each action and event that must occur to fulfill the requirements of run. The primary tab contains all information needed to perform a validated run.

In a previous iteration of this project I routed through early Twoson before inadequacies in project organization led me to scrap that route and go back to the drawing board. I have drafted a new route with better fundamentals, and better supporting materials, that is currently routed through Onett (https://www.youtube.com/watch?v=BfnYmuUwrk4)

## Next Steps
* Continue routing the run. Next milestones/chunks:
    * Twoson, first visit (through to Peaceful Rest Valley)
    * Peaceful Rest Valley and Happy Happy Village
    * Twoson, second visit (through to Threed)
    * Threed, first visit
    * Winters
* Write a data validation algorithm
    * Lua script to collect visited addresses
    * Python script to analyze visited addresses against all dialogue
* Write an annotations script
    * Lua script that displays onscreen text when certain addresses are visited