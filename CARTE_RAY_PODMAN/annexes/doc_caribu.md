### Quelques définitions importantes avant de commencer :

- rayonnement intercepté : quantité totale de rayonnement reçu par un objet
- rayonnement absorbé : rayonnement reçu - rayonnement transmis - rayonnement réfléchi
- réflectance : ratio du rayonnement reçu qui sera réfléchi par l'objet
- transmittance : ratio du rayonnement reçu qui va traverser l'objet (= transparence)
- capteur (sensor) : objet de caribu entièrement transparent, qui n'a donc aucun impact sur la scène mais qui permet de mesurer le rayonnement intercepté à différents endroits

### Utilisation basique de caribu :

Pour fonctionner, caribu nécessite une **scène**, composée des objets à éclairer, 
et une ou plusieurs **sources lumineuses**.
La scène peut être soit une scène créée avec PlantGl, soit une scène 
créée manuellement et composée de triangles, eux-mêmes composés de trois points ayant chacun des coordonnées x, y et z
pour les placer dans l'espace.

**important** : Pour orienter la scène dans l'espace, Caribu considère que **l'axe x+ pointe vers le Nord**.

L'exemple ci-dessous construit une scène valide 
qui représente un carré de 1m de côté placé à plat :

```python
triangle1 = [(0, 0, 0), (0, 1, 0), (1, 0, 0)]
triangle2 = [(1, 0, 0), (1, 1, 0), (0, 1, 0)]
scene = {
        "square" : [triangle1, triangle2]
    }
```

Les sources lumineuses peuvent aussi être définies manuellement, sous la forme
d'un tuple (intensité par m2, (vecteur directeur normé x y z)).
Il existe des librairies que l'on peut importer pour générer automatiquement 
le soleil ou le ciel.

```python
from alinea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun

### génération du soleil

energy = 1000
day_of_year = 72 # faire une boucle pour chaque jour de l'année
hour = 9 # faire une boucle pour chaque heure de la journée
latitude = 46.4
sun =  Gensun.Gensun()(energy, day_of_year, hour, latitude)
sunlight = GetLightsSun.GetLightsSun(sun)
## Passage au format Caribu
sun_str_split = sunlight.split(' ')
sun_intensity = float(sun_str_split[0])
sun_direction = tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))
direct_light = tuple((sun_intensity * 1, sun_direction))
# utiliser la variable [direct_light]

### génération du ciel

energy = 1000
type_of_sky = 'soc' # 'soc'=standard sky / 'uoc'=ultraviolet sky
nb_secteurs_azimuth = 12
nb_secteurs_zenith = 9
sky_string = GetLight.GetLight(GenSky.GenSky()(energy, type_of_sky, nb_secteurs_azimuth, nb_secteurs_zenith))
## Passage du format "string" au format "list" pour être compatible avec le format demandé par CaribuScene
sky = []
for string in sky_string.split('\n'):
    if len(string) != 0:
        string_split = string.split(' ')
        intensity = float(string_split[0])
        direction = tuple((float(string_split[1]), float(string_split[2]), float(string_split[3])))
        source = tuple((intensity, direction))
        sky.append(source)
# utiliser la variable sky
```

Une fois que la scène et les sources lumineuses sont définies, on peut lancer les calculs :

```python
carib_scene = CaribuScene(scene=scene, light=light_sources)
raw, aggregated = carib_scene.run(direct=True, screen_size=768)
```

Détail des paramètres de CaribuScene :

- scene
- light (list) : liste des sources lumineuses

paramètres optionnels :

- pattern (tuple) : coordonnées x et y du motif de base qui pourra être répété (x_min, y_min, x_max, y_max). Il sera découpé dans la scène et répété avec les sources lumineuses.
- opt (dict) : propriétés optiques des objets. 2 méthodes : fournir une texture (une réflectance et une transmittance par face), qui sera appliquée à tous les objets, ou fournir une texture par objet de la scène, par identifiant
- soil_reflectance (dict) : taux de réflectance du sol
- soil_mesh (int) : nombre de triangles composant le sol d'un pattern (-1 pour pas de sol). Je crois que cette option n'a pas été implémentée.
- z_soil (float) : hauteur du sol (par défaut, il sera sous l'objet le plus bas)
- scene_unit (str) : unité de mesure des distances (par défaut, mètres)

Détail des paramètres de la fonction run :

- direct (bool) : true par défaut, mettre false pour tenir compte des rayonnements rediffusés (transmis et réfléchis)
- infinite (bool) : false par défaut, mettre true pour activer la scène infinie (répétitions infinies du pattern précisé dans CaribuScene()). Si infinite est true, les calculs tiendront compte du fait que le motif est entouré de répétitions infinies de lui-même.
- d_sphere (float) : optionnel, diamètre (en m) d'une sphère autour de chaque objet dans laquelle le mode de calcul est différent
- layers (int) : optionnel, nombre de couches horizontales
- height (float) : hauteur (en m) de la canopée, par défaut, hauteur de l'objet le plus haut de la scène
- screen_size (int) : taille (longueur x largeur) en nb de pixels de l'écran de projection (= photo de la scène prise du point de vue de la source lumineuse, servant de base au calcul du rayonnement intercepté : 1 calcul par pixel)
- screen_resolution (float) : taille réelle (en m) d'1 pixel de l'écran de projection, paramètre à utiliser à la place du screen_size
- sensors (dict de listes de listes de tuples) : dictionnaire définissant les capteurs virtuels, objets invisibles servant à faire des mesures à un endroit précis
- split_face (bool) : false par défaut, mettre true pour afficher les résultats sur les 2 faces (sinon on aura juste les résultats de la face supérieure)
- simplify (bool) : simplification possible pour une simulation monochrome, false par défaut

Sorties de run():

- raw : dict de dicts représentant le rayonnement intercepté pour chaque triangle de chaque objet
- aggregated : résultats aggrégés par objet
	- area (float) : surface en m2
	- Eabs (float) : quantité de rayonnement absorbé rapporté à la surface (par m2)
	- Ei (float) : rayonnement intercepté rapporté à la surface (par m2)
	si split_face est true :
		- Ei_inf (float): quantité de rayonnement intercepté sur la face inférieure
		- Ei_sup (float): quantité de rayonnement intercepté sur la face supérieure
		- sensors (dict de dicts): Ei par sensor, groupés par id

Pour en savoir plus et visiter le code source, commenté en anglais :
https://github.com/openalea-incubator/caribu/blob/master/src/alinea/caribu/CaribuScene.py

Pour apprendre à créer une scène PlantGl :
https://plantgl-fb.readthedocs.io/en/latest/contents.html

Un tuto pour installer OpenAlea qui vous sera utile :
https://openalea.readthedocs.io/en/latest/install.html