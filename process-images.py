import os
import csv
from wand.color import Color as wandColor
from wand.image import Image as wandImage
from collections import OrderedDict
from pprint import pprint

CD = os.path.dirname(os.path.realpath(__file__))
notrim_directory = 'resources/maps/export-layers_output_flat/'
retrim_directory = 'resources/maps/process-images_output/'

regions = os.listdir(os.path.join(CD, notrim_directory))
region_dict = OrderedDict()

temp_count = 0
for region in regions:
    attributes = OrderedDict()
    with(wandImage(filename=os.path.join(CD, notrim_directory, region))) as img:
        img.trim(color=wandColor('rgba(0,0,0,0)'), fuzz=0)
        attributes['filename'] = region.replace('.png', '')
        attributes['size_x'], attributes['size_y'] = img.size
        attributes['x0'], attributes['y0'] = img.page[2:]
        attributes['x1'] = attributes['x0'] + attributes['size_x']
        attributes['y1'] = attributes['y0'] + attributes['size_y']
        attributes['hierarchy_level'] = len(region) - len(region.replace("_", ""))
        new_filename = f"{attributes['x0']:05}" \
                       f"_{attributes['y0']:05}" \
                       f"_{attributes['x1']:05}" \
                       f"_{attributes['y1']:05}" \
                       f"_{attributes['filename']}.png"
        img.format = 'png'
        print(new_filename)
        img.save(filename=os.path.join(CD, retrim_directory, new_filename))
    region_dict[region] = attributes

sorted_regions = OrderedDict(sorted(region_dict.items(), key=lambda item: item[1]['hierarchy_level'], reverse=True))

region_values = list(sorted_regions.values())

with open(os.path.join(CD, 'resources/tables/' 'rooms_and_regions.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, region_values[0].keys())
    w.writeheader()
    w.writerows(region_values)
