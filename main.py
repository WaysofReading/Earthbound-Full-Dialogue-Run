import os
import sys
from pprint import pprint, pformat
import yaml
import re
from collections import OrderedDict
import csv
import json

sys.path.insert(0, './earthbound-full-dialogue-run')
from constants import flags

CD = os.path.dirname(os.path.realpath(__file__))
DECOMPILATION_FOLDER = '20230106_decompilation'
DECOMPILATION_PATH = os.path.join(CD, 'resources', 'decompilations', DECOMPILATION_FOLDER)

DIALOGUE_BLACKLIST = {'C50000': 'Shop Case/Switch - Intro',
                      'C50198': 'Shop Case/Switch - Goodbye (Buy or sell)',
                      'C50330': 'Shop Case/Switch - Goodbye (~Buy or sell)',
                      'C504C8': 'Shop Case/Switch - Intro Question',
                      'C50660': 'Shop Case/Switch - Item Confirm',
                      'C507F8': 'Shop Case/Switch - Recipient Confirm',
                      'C50990': 'Shop Case/Switch - Equip It Here Prompt',
                      'C50A72': 'Shop Case/Switch - Buy Old Equipment Prompt',
                      'C50B54': 'Shop Case/Switch - Unequippable Warning',
                      'C50C36': 'Shop Case/Switch - Unequippable Decline Response',
                      'C50DCE': 'Shop Case/Switch - Not Enough Money',
                      'C50F66': 'Shop Case/Switch - Carrying Too Much',
                      'C510FE': 'Shop Case/Switch - Sell Question',
                      'C511E0': 'Shop Case/Switch - Sell Offer',
                      'C51568': 'Shop Case/Switch - Old Equipment Sold Thank You',
                      'C51700': 'Shop Case/Switch - Need More Prompt',
                      'C5197A': 'Shop Case/Switch - Alternate Recipient',
                      'C5E069': 'Shop Logic - Old Equipment Sold Loop',
                      'C5E1D6': 'Shop Logic - Bought Weapon?',
                      'C5E3BC': 'Shop Logic - Skip Sandwich?',
                      'C5E0A9': 'Shop Logic - Master Trunk?',
                      'C5EE13': 'Buzz Buzz Speech - Yes',
                      'C5EDD4': 'Buzz Buzz Speech - No',
                      'C5D5AB': 'Shop Case/Switch - Shop Menu',
                      'C5DF05': 'Shop Case/Switch - Buy Menu',
                      'C5DF3A': 'Shop Case/Switch - Sell Menu',
                      'C5E1AD': 'Shop Case/Switch -  Goodbye Fallthrough?',
                      'C5F39D': 'Buzz Buzz Dying - No',
                      'C5F564': 'Buzz Buzz Dying - Yes > Yes',
                      'C5F4F4': 'Buzz Buzz Dying - Yes > No',
                      'C607AE': 'Sanchez Bros - Yes > No Money',
                      'C607A5': 'Sanchez Bros - No',
                      'C607E4': 'Sanchez Bros - Yes > Has Money',
                      'C62E6D': 'ATM - Withdrawal Menu',
                      'C62D93': 'ATM - Deposit Menu',
                      'C630A8': 'Function - Phone',
                      'C63229': 'Phone Call - Dad',
                      'C6474F': 'Escargo Express - Store',
                      'C6483C': 'Escargo Express - Check Out',
                      'C64E04': 'Returns Counter - Master Trunk?',
                      'C6505D': 'Tenda Village - Horn of Life Shop',
                      'C6530C': 'Moneychanger - Yes',
                      'C652F1': 'Moneychanger - No',
                      'C65713': 'Moneychanger - Agree',
                      'C656F5': 'Moneychanger - Disagree',
                      'C685DA': 'Function - Jeff Repairs',
                      'C68C3F': 'Sleep Dialogue - PAULA_TELEPATHY_DREAM_1',
                      'C68CC3': 'Sleep Dialogue - PAULA_TELEPATHY_DREAM_2',
                      'C68D5A': 'Sleep Dialogue - PAULA_TELEPATHY_DREAM_JEFF',
                      'C695BA': 'Function - Ness Homesickness Checks',
                      'C6E33A': 'Dynamic Dialogue - Pokey to Ness',
                      'C6E36D': 'Dynamic Dialogue - Pokey to ~Ness',
                      'C6E426': 'Dynamic Dialogue - Pokey Kicks Party Out',
                      'C70329': 'Case/Switch - Hint Man Hint Selector',
                      'C7030F': 'Dynamic Dialogue - Hint Man Hint',
                      'C733A7': 'Dynamic Dialogue - Librarian - Yes - No Space',
                      'C73296': 'Dynamic Dialogue - Librarian - No',
                      'C75EBC': 'Conversation - Pokey Accept Invitation',
                      'C75E1C': 'Conversation - Pokey Decline Invitation',
                      'C7DC7F': 'Function - Check KO/Diamondized Status',
                      'C7DC85': 'Function - Check KO/Diamondized Status',
                      'C7D8EE': 'Present Case/Switch - No Contents',
                      'C7D92A': 'Present Case/Switch - Has Contents',
                      'C7D967': 'Dynamic Dialogue - Add Item to Other\'s Stuff',
                      'C7DD4F': 'Dynamic Dialogue - Yes/No - Options',
                      'C7DD5E': 'Dynamic Dialogue - Yes/No - Menu',
                      'C81751': 'Halting Issue - Apple Kid ~Give Food Dialogue',
                      'C81789': 'Halting Issue - Apple Kid Give Food Menu',
                      'C841DE': 'Case/Switch - Newspaper Headline',
                      'C90FB1': 'Sleep Dialogue - ZOMBIE_PAPER_ON_TENT',
                      'C91582': 'Function - Sleep for the Night',
                      'C915E1': 'Function - Phase Distorter - Repair',
                      'C91805': 'Healer Menu',
                      'C90FEC': 'Doctor Menu',
                      'C935B7': 'Player Name Prompt - Tenda Village',
                      'C9C19B': 'Phase Distorter - Lever - Yes',
                      'C9C15F': 'Phase Distorter - Lever - No > No'
                      }

class GameData:
    def __init__(self, target_decompilation):
        self.target_decompilation = target_decompilation
        self.npcs = {}
        self.map_sprites = {}
        self.raw_script = ''

        with open(os.path.join(self.target_decompilation, 'npc_config_table.yml')) as f:
            self.npcs = yaml.safe_load(f)

        with open(os.path.join(self.target_decompilation, 'map_sprites.yml')) as f:
            self.map_sprites = yaml.safe_load(f)

        with open(os.path.join(self.target_decompilation, "_cleanscript", "b.txt")) as f:
            self.raw_script = f.read()

        self.indexed_script = self.parse_raw_script()
        self.append_npc_locations()
        self.append_npc_dialogue()
        self.dereference_all_dialogue()
        self.label_sprites()
        self.label_flags()

    def parse_raw_script(self):
        # Generate (overlapping!) script groups:
        # -- Every group that starts with "; $FFFFFF" and ends with "[END]"
        # -- Every group that starts with "Npc####:" and ends with "[END]"

        script_tags_hex = re.findall(r'(?=\; \$([0-9A-F]{6})(.+?\[END\]))',
                                     self.raw_script,
                                     re.M | re.DOTALL)
        
        script_tags_npc = re.findall(r'(?=(Npc[0-9]{4})\:(.+?\[END\]))',
                                     self.raw_script,
                                     re.M | re.DOTALL)

        script_tags = script_tags_hex + script_tags_npc

        indexed_script = {idx: [block for block in content.split('\n') if block] for idx, content in script_tags}
        return indexed_script

    def append_npc_locations(self):
        # requires list_of_regions.csv output from utilities/map-splitter-namer/process-images
        with open(os.path.join(CD, 'resources', 'rooms_and_regions.csv')) as f:
            reader = csv.DictReader(f)
            # Cast cells of length <= 5 to int, leave others alone (see data file)
            list_of_regions = [{k: int(v) if len(v) <= 5 else v for k, v in row.items()} for row in reader]

        # Sprites definitions are listed for each map y- and x-sector in the decompilation
        for y_sector_number, x_sectors in self.map_sprites.items():
            for x_sector_number, sprites in x_sectors.items():
                if not sprites: continue
                for sprite in sprites:
                    x_pixel_abs = x_sector_number * 256 + sprite['X']
                    y_pixel_abs = y_sector_number * 256 + sprite['Y']

                    self.npcs[sprite['NPC ID']].update(
                        x_pixel_abs=x_pixel_abs,
                        y_pixel_abs=y_pixel_abs,
                        x_tile=int((x_sector_number * 256 + sprite['X']) / 32),
                        y_tile=int((y_sector_number * 256 + sprite['Y']) / 32),
                        x_sector=x_sector_number,
                        y_sector=y_sector_number,
                        x_sector_offset=sprite['X'],
                        y_sector_offset=sprite['Y'],
                        map_location_label="Unknown"
                    )

                    # use the list_of_regions.csv to associate an NPC with a named region
                    for region in list_of_regions:
                        inbounds = (region['x0'] <= x_pixel_abs <= region['x1']
                                    and region['y0'] <= y_pixel_abs <= region['y1'])
                        if inbounds:
                            self.npcs[sprite['NPC ID']]['map_location_label'] = region['filename']
                            break
        return

    def append_npc_dialogue(self):
        # Convert the dialogue pointer to hex to retrieve dialogue from the indexed script
        for _, npc in self.npcs.items():
            dialogue_1_pointer_raw = npc['Text Pointer 1']
            dialogue_2_pointer_raw = npc['Text Pointer 2']
            dialogue_1_pointer_hex = re.search(r'0x([0-9a-f]{6})', dialogue_1_pointer_raw)
            dialogue_2_pointer_hex = re.search(r'0x([0-9a-f]{6})', dialogue_2_pointer_raw)
            dialogue_1_pointer = dialogue_1_pointer_hex.group(1).upper() if dialogue_1_pointer_hex else None
            dialogue_2_pointer = dialogue_2_pointer_hex.group(1).upper() if dialogue_2_pointer_hex else None

            # Not sure why I chose to do it this way
            npc.update(
                dialogue_1_pointer=dialogue_1_pointer,
                dialogue_2_pointer=dialogue_2_pointer,
                dialogue_1=self.indexed_script[dialogue_1_pointer] if dialogue_1_pointer else None,
                dialogue_2=self.indexed_script[dialogue_2_pointer] if dialogue_2_pointer else None
            )

    def label_sprites(self):
        # Appends NPC labels from required 'sprite_groups.csv' by NPC ID
        with open(os.path.join(CD, 'resources', 'sprite_groups.csv')) as f:
            reader = csv.reader(f)
            next(reader)  # pop header row
            sprite_groups = {int(rows[0]): rows[1] for rows in reader}

        for npc_id, npc in self.npcs.items():
            npc['sprite_label'] = sprite_groups[npc['Sprite']]

        return

    def label_flags(self):
        # Appends flag labels from required 'flags.py' (credit: CataLatas)
        for npc_id, npc in self.npcs.items():
            try:
                npc['flag_label'] = flags.FLAG_NAMES[npc['Event Flag']]
            except KeyError:
                npc['flag_label'] = 'Unknown Flag'

    def dereference_all_dialogue(self):
        # Iterator for recursively derefencing each NPC's dialogue
        for npc_id, npc in self.npcs.items():
            
            npc['dialogue_1_dereferenced'], _ = self.dereference_dialogue(npc['dialogue_1']) if npc['dialogue_1'] else (None, None)
            npc['dialogue_2_dereferenced'], _ = self.dereference_dialogue(npc['dialogue_2']) if npc['dialogue_2'] else (None, None)
            
            d1_size = len(pformat(npc['dialogue_1_dereferenced']))
            d2_size = len(pformat(npc['dialogue_2_dereferenced']))

            if d1_size >= 100000:
                print(npc_id, 1, len(pformat(npc['dialogue_1_dereferenced'])))
            if d2_size >= 100000:
                print(npc_id, 2, len(pformat(npc['dialogue_2_dereferenced'])))
        return

    def dereference_dialogue(self, dialogue, depth=0, addresses_visited=[], max_depth=6):
        # Opaque-slow-and-fucked-up-but-mostly-works recursive function

        dereferenced_dialogue = OrderedDict()
        if depth >= max_depth or not dialogue:
            return dereferenced_dialogue, list(set(addresses_visited))

        for line in dialogue:
            dialogue_references = re.findall(r'L_([0-9A-F]{6})', line) + re.findall(r'(Npc[0-9]{4})', line)

            # Seems redundant, presumably I wrote it this way for a reason...
            if re.match(r'^L_[0-9A-F]{6}:$', line) or re.match(r'^Npc[0-9]{4}:$', line) or not dialogue_references:
                dereferenced_dialogue[line] = None
                continue

            for address in dialogue_references:

                unique_key = "{}:{}".format(line, address)
                target_dialogue = self.indexed_script[address] if address in self.indexed_script else OrderedDict()
                addresses_visited.append(address)

                if address not in DIALOGUE_BLACKLIST.keys():
                    recursed_dialogue, recursed_addresses = self.dereference_dialogue(target_dialogue, depth + 1, addresses_visited)
                    # try:
                    #     recursed_dialogue.popitem(last=False) #Trying to get rid of extraneous address notation
                    # except KeyError:
                    #     pass
                else:
                    recursed_dialogue = OrderedDict()
                    recursed_dialogue = DIALOGUE_BLACKLIST[address]
                    recursed_addresses = [address]
                addresses_visited = list(set(addresses_visited + recursed_addresses))
                dereferenced_dialogue[unique_key] = recursed_dialogue
        return dereferenced_dialogue, list(set(addresses_visited))

    def extract_flags_from_dialogue(self):
        for npc_id, npc in self.npcs.items():
            named_flags = []
            for _, label in flags.FLAG_NAMES.items():
                named_flags += [label] if label in npc['dialogue_1_dereferenced'] else []
                named_flags += [label] if label in npc['dialogue_2_dereferenced'] else []
            self.npcs[npc_id]['flags_referenced'] = ';'.join(named_flags)

    def print_details(self, npc_id):
        npc = self.npcs[npc_id]
        selection = OrderedDict([
            ('NPC ID', npc_id),
            ('NPC Sprite', npc['sprite_label']),
            ('Event Flag Label', npc['flag_label']),
            ('Visibility Condition', npc['Show Sprite']),
            ('dialogue 1', npc['dialogue_1_dereferenced']),
            ('dialogue 2', npc['dialogue_2_dereferenced']),
            ('Position (px)', "x: {} y: {}".format(npc['x_pixel_abs'], npc['y_pixel_abs']))
        ])
        pprint(selection, width=160)
        return

    def dump_npc_table(self):
        rows = []
        for k, v in self.npcs.items():
            if k == 0: continue
            flag_condition = v['Show Sprite']
            flag_condition_short = flag_condition
            if flag_condition == 'when event flag unset':
                flag_condition_short = 'unset'
            elif flag_condition == 'when event flag set':
                flag_condition_short = 'set'

            row = dict(npc_id=k,
                       npc_type=v['Type'],
                       sprite=v['Sprite'],
                       sprite_label=v['sprite_label'],
                       flag_condition="{}: {}".format(flag_condition_short, v['flag_label'])
                       )

            try:
                row['x_tile'] = v['x_tile']
                row['y_tile'] = v['y_tile']
                row['x_pixel_abs'] = v['x_pixel_abs']
                row['y_pixel_abs'] = v['y_pixel_abs']
                row['map_location_label'] = v['map_location_label']
            except KeyError:
                row['x_tile'] = None
                row['y_tile'] = None
                row['x_pixel_abs'] = None
                row['y_pixel_abs'] = None
                row['map_location_label'] = None
            rows.append(row)

        keys = rows[0].keys()

        with open(os.path.join(gd.target_decompilation, '_cleanscript', 'npc_values.csv'), 'w',
                  newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(rows)

    def dump_json(self):
        with open(os.path.join(self.target_decompilation, '_cleanscript', 'flat_dialogue_new.json'), 'w') as outfile:
            json.dump(self.npcs, outfile, indent=4)


if __name__ == '__main__':
    gd = GameData(DECOMPILATION_PATH)
    gd.dump_npc_table()
    gd.dump_json()
