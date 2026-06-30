#Importation packages
import imageio.v3 as iio
from pathlib import Path
import numpy as np

### IMPORTATION IMAGES
path=str(Path.cwd())
rc_panel = [f"C:/Users/mbabity/Documents/PlantGL/RS_PANEL/RC_P_{i}.png" for i in range(1,20) ]
rc_plant=[f"C:/Users/mbabity/Documents/PlantGL/RS_PLANT/RS_PL_{i}.png" for i in range(1,22) ]
mapping=[f"C:/Users/mbabity/Documents/PlantGL/MAPPING_CARIBU/GIF_MAPPING/mapping_{i}.png" for i in range(6,18) ]

mapping1=[]
gif_rc_plant=[]
for image in mapping:
    mapping1.append(iio.imread(image))

for image in rc_plant:
    gif_rc_plant.append(iio.imread(image))
    

import numpy as np
from PIL import Image

def create_gif(image_list, output_name):
    if not image_list: return
    
    first_image = Image.fromarray(image_list[0])
    target_size = first_image.size 
    
    processed_images = []
    for img_array in image_list:
        img = Image.fromarray(img_array)
        if img.size != target_size:
            # On redimensionne si nécessaire
            img = img.resize(target_size, Image.Resampling.LANCZOS)
        processed_images.append(np.array(img))
    
    iio.imwrite(output_name, processed_images, duration=400, loop=0)

# Appliquez-le à vos listes
create_gif(mapping1, "mapping_1.gif")
create_gif(gif_rc_plant, "rc_plant.gif")

import os
print("Fichier Panel existe :", os.path.exists("rc_panel.gif"))
print("Fichier Plant existe :", os.path.exists("rc_plant.gif"))


from PIL import Image

img = Image.open(r"C:\Users\mbabity\Documents\PlantGL\RS_PANEL\RC_P_1.png").convert("RGBA")

# remplacer blanc par noir (simple)
data = img.getdata()
new_data = []

for pixel in data:
    if pixel[:3] == (255,255,255):
        new_data.append((0,0,0,255))
    else:
        new_data.append(pixel)

img.putdata(new_data)
img.save("scene_black.png")