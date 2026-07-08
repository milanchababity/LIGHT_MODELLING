import numpy as np
from scipy import misc
import  matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image

## 

path = r"C:\Users\mbabity\Documents\PlantGL\PLANT.png"
image =Image.open(path).convert("RGB")
data=np.array(image)

# Masque pour le ROUGE (Plantes) : R élevé, G et B faibles
#mask_rouge = (data[:,:,0] > data[:,:,1] * 1.2) & (data[:,:,0] > data[:,:,2] * 1.2)
diff_rg = np.abs(data[:,:,0].astype(int) - data[:,:,1].astype(int))
diff_rb = np.abs(data[:,:,0].astype(int) - data[:,:,2].astype(int))
mask_gris = (diff_rg < 15) & (diff_rb < 15) & (data[:,:,0] > 40)

# 3. Appliquer les transformations via les masques
data[mask_gris] = [255, 255, 255] # On force le fond en BLANC
#data[mask_rouge] = [0, 255, 0]    # On force les plantes en VERT

resultat = Image.fromarray(data)
resultat.save("Plant_BLANC.png")
resultat.show()
  
  
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import numpy as np

# 1. Charger les données depuis le fichier JSON
nom_fichier = r'C:\Users\mbabity\Documents\PlantGL\simulation_Rc_Rs_panel_2.json' # Remplacez par le nom de votre fichier
with open(nom_fichier, 'r') as f:
    data = json.load(f)

print(data["Ratio_Rc_Rs"].values())
data_values=list(data["Ratio_Rc_Rs"].values())
toutes_les_valeurs = np.array(data_values)
v_min = toutes_les_valeurs.min()


fig, (ax_img, ax_cb) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [15, 1]}, figsize=(12, 6))
# 3. Afficher votre image PLANT_BLANC.png
img = mpimg.imread('PLANT_BLANC.png')
ax_img.imshow(img)
ax_img.axis('off') # Cache les axes de l'image

# 4. Créer la barre verticale (Colorbar)
norm = Normalize(vmin=v_min, vmax=v_max)
sm = cm.ScalarMappable(norm=norm, cmap='jet')

cb = plt.colorbar(sm, cax=ax_cb)
cb.set_label('Red/Far Red', rotation=270, labelpad=15)

plt.tight_layout()
plt.show()