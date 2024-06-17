# Earthbound Full Dialogue Run

## Introduction
A full-dialogue run of Earthbound is a playthrough of the Earthbound/MOTHER 2 (1994) in which every normally-accessible line of dialogue appears on-screen. “Normally-accessible” means lines of dialogue that are accessible without the use of glitches, cheats, or hacks. This includes all dialogue spoken by NPCs and displayed by objects (signs, doors, objects, etc.) For simplicity, battle-only text and item descriptions are excluded from the completion checklist.

I have been developing this run since March 2023. This repository includes the route itself (`resources\routes\Earthbound Full Dialogue Run - Route.xlsx`), as well as a number of materials and resources I've created to support development and tracking of this long, complex run.

Note: I am developing this route as though it were a speedrun; however, this project is also an exercise in exploring certain ideas I'm interested in around video game writing and unconventional modes play.  As such, I am as interested in actually executing the route as I am in analyzing the game and the process of developing this run. A bit of non-technical discussion can be found in the `docs\` directory of the repository, and some published posts on the project are available at (https://waysofreading.substack.com/p/full-dialogue-run-revisited).

 It is certain that  the route, once completed, will contain errors and omissions -- it's also the case that some dialogue is entirely inaccessible through normal play. Validation of a given run is a complex topic, Therefore, Therefore, it may make more sense to title the run "Maximum Dialogue", and to improve coverage in future iterations. 

## The Run
The run itself is being composed in `routes\Earthbound Full Dialogue Run - Route.xlsx` in this. The sheet includes one row for each action and event that must occur to fulfill the requirements of run. The primary tab contains all information needed to perform a validated run.

### Recordings
I have uploaded recordings of several segments of the run. Note that these are proof-of-concept recordings and I make use of emulator save states, pausing, and rewinding in order to create a faster, more watchable segment. I do not use these features to exploit glitches or take any action not possible for a skilled player.

*[Segment 01 - Onett](https://www.youtube.com/watch?v=BfnYmuUwrk4)
*[Segment 02 - Twoson](https://www.youtube.com/watch?v=uB2PgbbQon8)
*[Segment 03 - Happy Happy Village and Runaway 5](https://www.youtube.com/watch?v=p4cNvKl3Bk0)

## Text Access Monitor
As noted in the introduction, this is a long, complex run. It is expected to comprise several thousand steps that must be taken in a fairly precise order, with many cases where steps can be permanently missed due to the way NPC dialogue changes in response to plot events. This creates a challenge both for executing the run, and for __validating__ that the run has accomplished what it claims: visiting all normally-accessible NPC and object dialogue in the game.

In order to address these challenges, I have developed the Text Access Monitor, a LUA script for BizHawk (`text-access-monitor\text-access-monitor.lua`). This script exposes game state data to facilitate route development and execution, tracks overall run progress, and outputs a list of byte-level dialogue addresses accessed in a given `.bk2` recording of a run (to support validation and run completion calculations). The Text Access Monitor currently includes the following features:

* GAME STATS and PARTY
    * Money on hand and stored at the ATM
    * Map position
    * Emulation details (frame, time, speed, current input)
    * Timers for skip sandwich and Dad's "take a break?" phone calls
    * Party HP, PP, inventory slots open, and any status effects
* TEXT CALL STACK
    * Displays recent dialogue addresses pushed to the text parser registers
    * Also writes a list of all bytes and labels accessed to a text file (for run validation)
* ROUTE PROGRESS
    * Not fully implemented -- shows which dialogue has been accessed for several kinds of dialogue
        * Bytes: byte-level addresses of dialogue in game ROM (~327,680 bytes)
        * Labels: labeled sections of dialogue in game ROM (~6,153 labels)
        * Items: item descriptions (255 items)
        * Presents: trash cans, coffins, and presents with items (or nothing) (174 presents)
        * Photos: events where the party has their photo taken (32 photos)
        * Hints: hints shared by the Hint Man throughout the game (75 hints)
        * Headlines: Newspaper headlines after staying at hotels throughout the game (~93 headlines)
* ROUTE NEXT STEPS
    * Uses a CSV version of the route spreadsheet to display a scroll of past and upcoming steps
    * Controllable in-game by holding down Y and using Up, Down, Left, Right (+1, -1, +5, -5 steps)
* DIALOGUE HISTORY
    * Displays processed plaintexts which (should) correspond to recent dialogue labels accessed by the player
* RNG MONITOR
    * Snes9x version by pirohiko, BizHawk version by BrunoValads
    * Note: BrunoValads' code (https://pastebin.com/MRix5ZJg) served as the basis for the Text Access Monitor script

## Run Validation
It is impossible to reach 100% of all dialogue bytes and labels in Earthbound through normal play. Of the subset of dialogue data which _is_ normally accessible, it's virtually certain that the completed route will include a number of gaps, errors, and oversights. The route spreadsheet supports basic validation and includes tables showing whether and how often each NPC has been visited, as well as checklists for hints and newspaper headlines.

Given the length of a full run, it's also important to be able to automate the calculation of the completion rate ("collection rate") of a given run for progress tracking, as well as to identify gaps in coverage that necessitate revisions to the route. I'm currently thinking of the collection rate in terms of one of two formulae:

* The number of dialogue bytes accessed divided by the total number of bytes in game ROM
* The number of dialogue address labels accessed divided by the total number of addresses in game ROM

The Text Access Monitor includes features for tracking and logging both of these types of access, and can be used to establish how much of the total dialogue in the game was accessed in a run. A subtler question involves determining which addresses are truly unreachable: I will investigate this challenge later, once the initial route is drafted.

## Next Steps
* Record routed segments:
    * Threed (including Saturn Valley and Belch's Factory)
* Route remaining segments of the run:
    * Fourside 1 (Dusty Dunes + Mole Cave)
    * Fourside 2 (Paula's kidnapping + Moonside)
    * Summers
    * Scaraba
    * Deep Darkness
    * Stonehenge + Lost Underworld
    * Magicant
    * Onett + Cave of the Past
    * Postgame

## Repository Overview
* `docs\` Documentation of various processes used for creation of the run and supporting materials
    * `process-guide_create-region-images_20230701.txt` Guide to creating image files for Earthbound's individual rooms and overworld regions
* `resources\` Data, documentation, and materials relating to the run
    * `decompilations\` Decompiled data from the Earthbound game ROM
        * `20230106\` A CoilSnake decompilation that is my source for all outputs inventoried here
    * `dialogue\` Text files containing game dialogue in various arrangements
        * `addresses.txt` A list of all dialogue address labels in game ROM
        * `process-dialogue_output.json` Output from process-dialogue.py (uses `script-dumper_output.txt`)
        * `process-dialogue_output.csv` Flattened from process-dialogue.py (used by `text-access-monitor.lua`)
        * `script-dumper_output.txt` Output from Earthbound Script Dumper
        * `script-dumper_output_text-only.txt` Output from Earthbound Script Dumper, plaintext only
        * `by_npc\` Output from process-dialogue.py, separate text file for each NPC
        * `by_npc_working-set\` Output from process-dialogue.py, free to modify for routing purposes
        * `ccscript_parts\` CCScript files from CoilSnake
    * `labels\` Tables mapping game values to text labels
        * `sprite-group-labels.csv/xlsx` Canonical or descriptive names for game sprites (used by `text-access-monitor.lua`)
    * `maps\` Image files for every overworld region and room in Earthbound, with number labels for sprites
        * `export-layers_output` Intermediate output (from antipalindrome, `Photoshop-Export-Layers-to-Files-Fast-2.7.1`)
        * `export-layers_output_flat` Same as above, with all image files in a single directory
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
        * `regions-trimmed-flat-by-name` Final output, separate image files for each region in the game
    * `ram-watches\` Files used by BizHawk to expose values of game RAM
        * `Earthbound (USA).wch` a RAM watch file for Earthbound
    * `recordings\` Emulator and video recordings of full runs and run segments
        * `bk2\` Bizhawk emulator movie files
        * `vid\` Video recordings for sharing and publication (too large for GitHub, look on YouTube)
    * `routes\` Materials for the Full Dialogue Run route
        * `Earthbound Full Dialogue Run - Route.xlsx` The most recent draft of the route
        * `_old\` Old routing files
        * `regions-trimmed-flat` Output from Bulk Rename Utility flattening `process-images_output`
        * `regions-trimmed-flat_by-name` Coordinates removed so list is sortable by name/hierarchy
        * `layers_all-regions-and-rooms.psd` (BIG) all rooms and segmented overworld regions in nested layer structure
        * `layers_overworld-regions-only.psd` Complete overworld regions only in flat layer structure
        * `map-with-npcs_spread_nogrid.png` output from EB Project Editor with NPCs shown (adjusted for visiblity)
    * `saves\` Save states created at various points along the route
        * `save-states_BSNES` For use with BizHawk's SubBSNESv115+ core
        * `sram` for use with BizHawk
    * `screenshots\` Screenshots of Earthbound created with BizHawk. Just for fun/reference.
    * `tables\` Automatically-generated value lists for game entities
        * `regions-and-rooms.csv` Names and coordinates for all regions and rooms (output from `process-images.py`)
        * `npcs.csv` Detailed table of all NPCs (output from `process-dialogue.py`)
        * `flags.csv` English labels for all numbered game flags (from CataLatas, `earthbound-script-dumper`)
* `text-access-monitor\` Multipurpose LUA script for facilitating run routing and validation. See "Text Access Monitor", above, for more details.
* `utilities\` Scripts, utilities, and tools. Supporting tools created by other authors as annotated below. 
    * `bizhawk_29\` Technical/TASing/Scripting emulator (https://tasvideos.org/BizHawk)
    * `coilsnake\` Earthbound decompilation and modification tool (https://pk-hack.github.io/CoilSnake/)
    * `earthbound-script-dumper-main\` Tool for refining dumped script (https://github.com/CataLatas/earthbound-script-dumper)
        * `constants\` includes English labels for flags, items, etc.
    * `Photoshop-Export-Layers-to-Files-Fast-2.7.1` Tool to split PSD by layer with options (https://github.com/antipalindrome/Photoshop-Export-Layers-to-Files-Fast)
    * `roms\` This run is based on an unmodified `EarthBound (USA).sfc` (CRC32 = `DC9BB451`)
* `process-images.py` Yields trimmed and renamed versions of images output from `Photoshop-Export-Layers-to-Files-Fast-2.7.1`
* `process-dialogue.py`. Recursively unrolls dumped script, and yields dialogue files and NPC tables

Additional documentation may be available in the Python source code and elsewhere.