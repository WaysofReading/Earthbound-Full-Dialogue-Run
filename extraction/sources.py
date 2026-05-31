import os

CD = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

DECOMPILATION = '20230106'
DECOMPILATION_PATH = os.path.join(CD, 'resources', 'decompilations', DECOMPILATION)

NPC_CONFIG_TABLE = os.path.join(DECOMPILATION_PATH, 'npc_config_table.yml')
MAP_SPRITES = os.path.join(DECOMPILATION_PATH, 'map_sprites.yml')
MAP_DOORS = os.path.join(DECOMPILATION_PATH, 'map_doors.yml')
PHOTOGRAPHER_CFG_TABLE = os.path.join(DECOMPILATION_PATH, 'photographer_cfg_table.yml')
ITEM_CONFIGURATION_TABLE = os.path.join(DECOMPILATION_PATH, 'item_configuration_table.yml')

SCRIPT_DUMPER_OUTPUT = os.path.join(CD, 'resources', 'dialogue', 'script-dumper_output.txt')
ADDRESSES_TXT = os.path.join(CD, 'resources', 'dialogue', 'addresses.txt')

ROOMS_AND_REGIONS_CSV = os.path.join(CD, 'resources', 'tables', 'rooms_and_regions.csv')
FLAGS_CSV = os.path.join(CD, 'resources', 'tables', 'flags.csv')
SPRITE_GROUP_LABELS_CSV = os.path.join(CD, 'resources', 'labels', 'sprite-group_labels.csv')

EXTRACTED_DIR = os.path.join(CD, 'resources', 'dialogue', 'extracted')
ENTITIES_DIR = os.path.join(EXTRACTED_DIR, 'entities')

NODES_JSON = os.path.join(EXTRACTED_DIR, 'nodes.json')
ENTITIES_JSON = os.path.join(EXTRACTED_DIR, 'entities.json')
VALIDATION_JSON = os.path.join(EXTRACTED_DIR, 'validation.json')
ANALYTICS_JSON = os.path.join(EXTRACTED_DIR, 'analytics.json')

LEGACY_DIALOGUE_CSV = os.path.join(CD, 'resources', 'dialogue', 'process-dialogue_output.csv')
LEGACY_NPCS_CSV = os.path.join(CD, 'resources', 'tables', 'npcs.csv')
