# Earthbound Full Dialogue Run
A full-dialogue run of Earthbound is a playthrough of the game in which every normally-accessible line of overworld and inventory dialogue appears on-screen. “Normally-accessible” means lines of dialogue that are accessible without the use of glitches, cheats, or hacks. Battle-only text such as enemy attacks or in-battle item usage are excluded.

This project repository serves to house and document materials used to develop this complex run.

Note: While I am working on this project as though it were a conventional speedrun, it is also an attempt to explore certain ideas around video game writing, identities, and unconventional play. As such, I am as interested in ways of interpreting this game, run, and route as I am in actually executing it. Additional non-technical discussion can be found in the `docs\` segment of the repository with published posts on at (https://waysofreadingblog.com/tags/earthbound).

## Repository Map

* `resources\` Data, information, and materials
    * `flat_dialog.json` Earthbound dialogue processed for ease of reading
    * `decompilation_20230106\` Decompiled game data from CoilSnake (https://pk-hack.github.io/CoilSnake/)
        * `_cleanscript\cleanscript.txt` Tidied version of the game script from `utilities\earthbound-script-dumper`
    * `regions-and-rooms_trimmed-flat\` Image files for each overworld region and room, named descriptively:
        * e.g. `06144_06016_06400_06144_Dusty Dunes Desert_Monkey Cave_Start_Left_Left-(Hallway)`
            * x0 (bounding box)
            * x1 (bounding box)
            * y0 (bounding box)
            * y1 (bounding box)
            * Area (English label)
            * SubArea (English label) ...
            * (Note)
            * .png
    * `map-sliced_202302011.psd` Nested cut Layers for each room and region on Earthbound map
        * **Not pushed due to size constraints - I can share on request**
    * `map-with-npcs_spread_nogrid.png` Earthbound map image file used in Photoshop file
    * `npc_values.csv` Table of NPCs combining data
        * from `sprite_groups.csv` (sprite + location details)
        * from `decompilations\...\npc_config_table.yml` (NPC details, CoilSnake output)
        * from `regions-and-rooms.csv` (location details)
    * `regions_and_rooms.csv` Table of rooms and overworld regions
    * `route.txt` Link to the current draft of the run route (Google Sheet)
    * `sprite_groups.csv` English names (Author: me) for each sprite in the `SpriteGroups` folder
* `utilities\` Scripts, utilities, and tools. Supporting tools created by other authors as annotated below. 
    * `bizhawk\` Technical/TASing/Scripting emulator (https://tasvideos.org/BizHawk)
    * `earthbound-script-dumper-main\` Tool for refining dumped script (https://github.com/CataLatas/earthbound-script-dumper)
        * `constants\` includes English labels for flags, items, etc. Invaluable.
    * `Photoshop-Export-Layers-to-Files-Fast-2.7.1` Tool to split PSD by layer with options (https://github.com/antipalindrome/Photoshop-Export-Layers-to-Files-Fast)
    * `map-splitter-namer\` Generates outputs for `resources\regions-and-rooms\`
    * `roms\` Expects `EarthBound (USA).sfc`
* `process-images.py` Trims, names, processes output from antipalindrome's tool (Author: me)
* `process-dialogue.py`. Recursively unrolls dumped script yielding `resources\flat_dialog.json` (Author: me)

Additional documentation may be available in the Python source code and elsewhere.

## The Run File
The run itself is documented on a Google Sheet linked in `resources\route.txt` in this repository, or accessible at (https://docs.google.com/spreadsheets/d/1W9WpMgIaLJZUDxKTG1n-6-2rl2r4qpdpA_hOta7AWX0). The sheet includes one row for each action and event that must occur to fulfill the requirements of run. The primary "main_sequence" tab contains the following fields:

* **Playthrough #**. The ordinal of the game playthrough where this action/event occurs. It is expected that fulfilling the requirements for a "Full Dialogue Run" will require multiple playthroughs.
* **Segment #**. The ordinal of the run segment of this action/event in the current playthrough
* **Step #**. The ordinal of this action/event in the current segment
* **Run Segment**. The English name of the segment of this run (TBD)
* **Step.** One of a set of actions or events designated on the `list_of_verbs` tab
* **Who?** The object of the verb ("NA" if there is no target in the world)
* **Where?** A location designated on the `list_of_regions` tab (from `regions_and_rooms.csv`)
* **With What?** Indirect object for the verb from `list_of_items` tab (from `constants\items.py`)
* **Requires**. Flag status(es) required to complete the action/event (from `constants\flags.py`)
    * `FLAG_NAME` means the flag must be SET
    * `~FLAG_NAME` means the flag must be UNSET
* **Sets**. Flags set as a result of this action/event
* **Unsets**. Flags unset as a result of this action/event
* **Address**. Some actions/events reference an address in ROM
* **Description**. Some actions/events require specification (e.g., select "Yes" or "No")
* **Note**. A note about this action/event of interest to the author or readers
* **NPC (Label)**. Look up on `Who?` via `npc_values`
* **Location (x,y)**. Look up on `Where?` via `list_of_regions`

Finally, the `to_slot` tab contains actions/events that will need to be slotted later in the route. The existence of unarranged actions/events is a side effect of the approach I've used for routing: namely, play through the game normally and fully document all dialogue for each NPC as one encounters them.

## Next Step
In a previous iteration of this project I routed through early Twoson before inadequacies in project organization led me to scrap that route and go back to the drawing board. I will have a good sense of how well my new approach can manage complexity by completing Earthbound's initial sizable segment, the city of Onett.

## Specific To-do Items
* `main.py` declares the `DIALOGUE_BLACKLIST` variable, which lists all dialogue pointers that may result in an infinite dialogue loop. These are avoided in the recursive `dereference_dialogue()` function, a necessary step for managing the size and readability of `flat_dialog.json`.
    * It may be useful to store and refer to these from out of `constants`, perhaps as `fixed_dialogue.py`, a somewhat broader term because many of the pointers on this list reference "fixed" dialogue used by multiple NPCs, such as hotel bellhops or doctors. Note that this run is "All Dialogue", not "All NPC", so it is conceivable that some NPCs may be skipped entirely if all their dialogue is covered by an earlier NPC.
* It is not clear how to segment/split the run and therefore the layout of `route.gsheet` is not settled. Robust 

## Open Question: Validation
This is a complicated run with thousands of required steps and a commensurately long expected completion time. Furthermore, the parameters are such that a performer's failure to complete any one of the steps could invalidate the entire run attempt.

Given these facts it's imperative to have a reasonable way of validating, to a high degree of accuracy, both the description of the run (`route.gsheet`) and any given performance of the run. This is an important question that is not yet along the critical path for the project. I've  discussed the matter to various levels of granularity over on the Ways of Reading blog [link, link, link].

It's likely the best validation solution will be to record attempts with BizHawk and write a LUA script that logs memory reads against all memory regions known to contain game dialogue, outputting a log that can be used to decide whether any required dialogue was skipped. Real-time monitoring may be possible with the resources I've created and additional time to brainstorm a LiveSplit/OBS-based solution.
