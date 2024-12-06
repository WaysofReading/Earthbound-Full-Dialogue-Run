import os
import json
import csv

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'process-dialogue_output.json')) as json_file:
    data = json.load(json_file)

new_output = []

for k, v in data.items():
    new_output.append(dict(
        address=v["d1_pointer"],
        address_alt=v["d2_pointer"],
        entity_id=k,
        sprite_label=v["sprite_label"],
        map_location_label=v["map_location_label"],
        entity_type=v["Type"]
    ))

keys = new_output[0].keys()

with open(os.path.join(__location__, 'npc-list.csv'), 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(new_output)
