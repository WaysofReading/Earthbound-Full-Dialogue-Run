import os
import sys
from pprint import pprint, pformat
import yaml
import re
from collections import OrderedDict
import csv
import json
from datetime import datetime

sys.path.insert(0, './utilities/earthbound-script-dumper')
from constants import flags

CD = os.path.dirname(os.path.realpath(__file__))
DECOMPILATION = '20230106'

DECOMPILATION_PATH = os.path.join(CD, 'resources/decompilations', DECOMPILATION)
DIALOGUE_FILE_PATH = os.path.join(CD, 'resources/dialogue', 'script-dumper_output.txt')

CURRENT_DATETIME = datetime.today().strftime('%Y%m%d_%H%M%S')

# An incomplete list of dialogue addresses that are
#   -- long
#   -- contain infinite loops
#   -- are frequently referenced or repeated
# To keep the script file manageable these references are substituted for content in the parser

DIALOGUE_BLACKLIST = {
    'C50000': 'Shop Case/Switch - Intro',
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
    'C6E33A': 'Loop - Pokey to Ness',
    'C6E36D': 'Loop - Pokey to ~Ness',
    'C6E426': 'Loop - Pokey Kicks Party Out',
    'C70329': 'Case/Switch - Hint Man Hint Selector',
    'C7030F': 'Loop - Hint Man Hint',
    'C733A7': 'Loop - Librarian - Yes - No Space',
    'C73296': 'Loop - Librarian - No',
    'C75EBC': 'Conversation - Pokey Accept Invitation',
    'C75E1C': 'Conversation - Pokey Decline Invitation',
    'C760B7': 'Conersation - Pokey Joins Script',
    'C7DC7F': 'Function - Check KO/Diamondized Status',
    'C7DC85': 'Function - Check KO/Diamondized Status',
    'C7D8EE': 'Present Case/Switch - No Contents',
    'C7D92A': 'Present Case/Switch - Has Contents',
    'C7D967': 'Loop - Add Item to Other\'s Stuff',
    'C7DD4F': 'Loop - Yes/No - Options',
    'C7DD5E': 'Loop - Yes/No - Menu',
    'C81751': 'Loop - Apple Kid ~Give Food Dialogue',
    'C81789': 'Loop - Apple Kid Give Food Menu',
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


NPC_FIELDS = [
    "Sprite",
    "sprite_label",
    "map_location_label",
    "Type",
    "flag_condition",

    "d1_pointer",
    "d1_flags",
    "d1_addresses",
    "d1_text",
    "d1_lines",
    "d1_unrolled",

    "d2_pointer",
    "d2_flags",
    "d2_addresses",
    "d2_text",
    "d2_lines",
    "d2_unrolled",
    
    "x_pixel_abs",
    "y_pixel_abs",
    "x_tile",
    "y_tile",
    "x_sector",
    "y_sector",
    "x_sector_offset",
    "y_sector_offset",

    "Event Flag",
    "flag_label",
    "Show Sprite",
    "Direction",
    "Movement",
    "Text Pointer 1",
    "Text Pointer 2"
]

class GameData:
    def __init__(self, decompilation, dialogue_file):
        self.decompilation = decompilation
        self.dialogue_file = dialogue_file
        self.raw_script = ''
        self.indexed_script = {}
        self.npcs = {}
        self.map_sprites = {}

        

        with open(os.path.join(self.decompilation, 'map_sprites.yml')) as f:
            self.map_sprites = yaml.safe_load(f)

        with open(self.dialogue_file) as f:
            self.raw_script = f.read()

        self.index_raw_script()
        self.load_npc_data()
        self.calculate_npc_locations()
        self.append_npc_dialogue()
        self.unroll_all_dialogue()
        self.label_sprites()
        self.label_flags()

    def index_raw_script(self):
        # raw_script is the text file output from earthbound-script-dumper
        # Generate overlapping script groups based on labels:
        # -- Every group that starts with "; $FFFFFF" and ends with "[END]"
        # -- Every group that starts with "Npc####:" and ends with "[END]"

        with open(self.dialogue_file) as f:
            self.raw_script = f.read()

        script_tags_hex = re.findall(r'(?=\; \$([0-9A-F]{6})(.+?\[END\]))',
                                     self.raw_script,
                                     re.M | re.DOTALL)
        
        script_tags_npc = re.findall(r'(?=(Npc[0-9]{4})\:(.+?\[END\]))',
                                     self.raw_script,
                                     re.M | re.DOTALL)

        script_tags = script_tags_hex + script_tags_npc

        for idx, content in script_tags:
            blocks = [block for block in content.split('\n') if block]
            self.indexed_script[idx] = blocks

    def initialize_npc_record(self, field_list):
        return {label:None for label in field_list}

    def load_npc_data(self):
        with open(os.path.join(self.decompilation, 'npc_config_table.yml')) as f:
            npc_data = yaml.safe_load(f)
        
        for npc_id, npc_record in npc_data.items():
            self.npcs[npc_id] = self.initialize_npc_record(NPC_FIELDS)
            self.npcs[npc_id].update(npc_record)
        return
    
    def calculate_npc_locations(self):

        # Read resources/list_of_regions.csv output from process-images.py
        list_of_regions = []
        with open(os.path.join(CD, 'resources', 'tables', 'rooms_and_regions.csv')) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Cast cells of length <= 5 to int
                region = {}
                for k, v in row.items():
                    try:
                        region[k] = int(v)
                    except ValueError:
                        region[k] = v
                list_of_regions.append(region)

        # Sprite definitions are organized by map y- and x-sector
        for y_sector, x_sectors in self.map_sprites.items():
            for x_sector, sprites in x_sectors.items():
                if not sprites: continue
                for sprite in sprites:
                    v = {
                        "x_pixel_abs": x_sector * 256 + sprite['X'],
                        "y_pixel_abs": y_sector * 256 + sprite['Y'],
                        "x_tile": int((x_sector * 256 + sprite['X']) / 32),
                        "y_tile": int((y_sector * 256 + sprite['Y']) / 32),
                        "x_sector": x_sector,
                        "y_sector": y_sector,
                        "x_sector_offset": sprite['X'],
                        "y_sector_offset": sprite['Y'],
                        'map_location_label': None
                    }

                    # Search the list of regions to assign the NPC to a named region
                    for region in list_of_regions:
                        inbounds = (region['x0'] <= v['x_pixel_abs'] <= region['x1']
                                    and region['y0'] <= v['y_pixel_abs'] <= region['y1'])
                        if inbounds:
                            v['map_location_label'] = region['filename']

                            break
                    self.npcs[sprite['NPC ID']].update(v)
        return

    def append_npc_dialogue(self):
        # Convert the dialogue pointer to hex to retrieve dialogue from the indexed script
        for _, npc in self.npcs.items():
            d1_pointer_raw = npc['Text Pointer 1']
            d2_pointer_raw = npc['Text Pointer 2']
            d1_pointer_hex = re.search(r'0x([0-9a-f]{6})', d1_pointer_raw)
            d2_pointer_hex = re.search(r'0x([0-9a-f]{6})', d2_pointer_raw)
            d1_pointer = d1_pointer_hex.group(1).upper() if d1_pointer_hex else None
            d2_pointer = d2_pointer_hex.group(1).upper() if d2_pointer_hex else None

            v = {
                'd1_pointer': d1_pointer,
                'd2_pointer': d2_pointer,
                'd1_text': '\r\n'.join(self.indexed_script[d1_pointer]) if d1_pointer else None,
                'd2_text': '\r\n'.join(self.indexed_script[d2_pointer]) if d2_pointer else None,
                'd1_lines': self.indexed_script[d1_pointer] if d1_pointer else None,
                'd2_lines': self.indexed_script[d2_pointer] if d2_pointer else None
            }
            npc.update(v)
        return

    def label_sprites(self):
        # Appends NPC labels from required 'sprite_groups.csv' by NPC ID
        with open(os.path.join(CD, 'resources/labels', 'sprite-group_labels.csv')) as f:
            reader = csv.reader(f)
            next(reader)  # pop header row
            sprite_groups = {int(rows[0]): rows[1] for rows in reader}

        for npc_id, npc in self.npcs.items():
            npc['sprite_label'] = sprite_groups[npc['Sprite']]

        return

    def label_flags(self):
        # Appends flag labels from 'flags.py' (CataLatas)
        for npc_id, npc in self.npcs.items():
            try:
                npc['flag_label'] = flags.FLAG_NAMES[npc['Event Flag']]
            except KeyError:
                npc['flag_label'] = 'Unknown Flag'

    def unroll_all_dialogue(self):
        # Iterator for recursively derefencing each NPC's dialogue
        for npc_id, npc in self.npcs.items():
            d1_unrolled = self.unroll_dialogue(npc['d1_lines'])
            prefixed_d1 = {'d1_' + k: v for k, v in d1_unrolled.items()}
            npc.update(prefixed_d1)

            d2_unrolled = self.unroll_dialogue(npc['d2_lines'])
            prefixed_d2 = {'d2_' + k: v for k, v in d2_unrolled.items()}
            npc.update(prefixed_d2)
        return

    def get_addresses_from_line(self, line):
        addresses = re.findall(r'L_([0-9A-F]{6})', line) + \
                    re.findall(r'(Npc[0-9]{4})', line)
        return addresses
    
    def get_flags_from_line(self, line):
        flags = []

        flags_beq = re.findall(r'GOTO_IF_FLAG (.+) L_([0-9A-F]{6})', line)
        for ref in flags_beq:
            description = '1. goto {} if {} is set'.format(ref[1], ref[0])
            flags += [description] if description not in flags else []

        flags_bne = re.findall(r'LOAD_FLAG (.+)\]\[GOTO_IF_FALSE L_([0-9A-F]{6})\]', line)
        for ref in flags_bne:
            description = '2. goto {} if {} is cleared'.format(ref[1], ref[0])
            flags += [description] if description not in flags else []

        flags_set = re.findall(r'SET_FLAG (.+)\]', line)
        for ref in flags_set:
            description = '3. set {}'.format(ref)
            flags += [description] if description not in flags else []
        
        flags_cls = re.findall(r'CLR_FLAG (.+)\]', line)
        for ref in flags_cls:
            description = '4. clear {}'.format(ref)
            flags += [description] if description not in flags else []
        
        return flags

    def unroll_dialogue(self, block, depth=0, max_depth=6):
        values = {
            'unrolled': OrderedDict(),
            'addresses': [],
            'flags': [],
        }

        if depth >= max_depth or not block:
            return values

        for line in block:
            flags = self.get_flags_from_line(line)
            addresses = self.get_addresses_from_line(line)
            values['flags'] += flags
            values['addresses'] += addresses
            is_hex_label = re.match(r'^L_[0-9A-F]{6}:$', line)
            is_npc_label = re.match(r'^Npc[0-9]{4}:$', line)

            if not addresses:
                values['unrolled'][line] = None
                continue
            elif is_hex_label or is_npc_label:
                continue

            for address in addresses:
                reference_key = "{}:{}".format(line, address)
                
                if address in DIALOGUE_BLACKLIST.keys():
                    values['unrolled'][reference_key] = DIALOGUE_BLACKLIST[address]
                    continue
                elif address not in self.indexed_script:
                    values['unrolled'][reference_key] = 'INVALID KEY'
                    continue
                else:
                    referenced_block = self.indexed_script[address]
                    referenced_values = self.unroll_dialogue(referenced_block, depth + 1)
                    values['unrolled'][reference_key] = referenced_values['unrolled']
                    values['addresses'] += referenced_values['addresses']
                    values['flags'] += referenced_values['flags']
        
        # Deduplicate and sort by alpha
        values['addresses'] = sorted(list(set(values['addresses'])))
        values['flags'] = sorted(list(set(values['flags'])))

        return values

    def print_details(self, npc_id):
        npc = self.npcs[npc_id]
        selection = OrderedDict([
            ('NPC ID', npc_id),
            ('NPC Sprite', npc['sprite_label']),
            ('Event Flag Label', npc['flag_label']),
            ('Visibility Condition', npc['Show Sprite']),
            ('dialogue 1', npc['dialogue_1_unrolled']),
            ('dialogue 2', npc['dialogue_2_unrolled']),
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
                flag_condition_short = '~' + v['flag_label']
            elif flag_condition == 'when event flag set':
                flag_condition_short = '' + v['flag_label']
            elif flag_condition == 'always':
                flag_condition_short = 'always'
            

            row = dict(npc_id=k,
                       sprite_label=v['sprite_label'],
                       npc_type=v['Type'],
                       sprite=v['Sprite'],
                       
                       flag_condition="{}: {}".format(flag_condition_short, v['flag_label'])
                       )

            row = {}
            row['npc_id'] = k
            row['sprite_label'] = v['sprite_label']

            try:
                row['map_location_label'] = v['map_location_label']
            except KeyError:
                row['map_location_label'] = None

            row['npc_type'] = v['Type']
            row['flag_condition'] = flag_condition_short
            row['sprite'] = v['Sprite']
            
            try:
                row['x_tile'] = v['x_tile']
                row['y_tile'] = v['y_tile']
                row['x_pixel_abs'] = v['x_pixel_abs']
                row['y_pixel_abs'] = v['y_pixel_abs']
                
            except KeyError:
                row['x_tile'] = None
                row['y_tile'] = None
                row['x_pixel_abs'] = None
                row['y_pixel_abs'] = None
            rows.append(row)

        keys = rows[0].keys()

        with open(os.path.join(CD, 'resources/tables/' 'npcs.csv'), 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(rows)

    def dump_json(self):
        with open(os.path.join(CD, 'resources/dialogue/', 'process-dialogue_output.json'), 'w') as outfile:
            json.dump(self.npcs, outfile, indent=2)
        
        for npc_id, npc in self.npcs.items():
            with open(os.path.join(CD, 'resources', 'dialogue', 'by_npc', f'{npc_id:0>4d}.json'), 'w') as outfile:
                json.dump(npc, outfile, indent=2)


if __name__ == '__main__':
    gd = GameData(DECOMPILATION_PATH, DIALOGUE_FILE_PATH)
    gd.dump_npc_table()
    gd.dump_json()
