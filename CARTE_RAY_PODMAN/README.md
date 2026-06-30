# Installation et mise en route :

## Prérequis :

Suivez toutes les étapes du README d'install_container

Une fois le container installé, récupérez dans install_container les 2 scripts install_mamba.sh et install_openalea.sh et, depuis votre PC, placez-les dans votre répertoire de travail partagé entre votre PC et le container (celui que vous avez choisi à la création du container)

## Dans le terminal du container :

Si vous avez oublié le nom de votre répertoire de travail partagé, vous pouvez le retrouver avec la commande :
> ls

Exécutez ensuite les commandes suivantes :

> cd {nom_de_votre_répertoire_partagé}

> ./install_openalea.sh alinea.caribu matplotlib requests openalea.plantgl

#### Fermer la fenêtre du terminal.

#### Rouvrez un terminal Debian.

> podman.exe machine start

Si vous avez oublié le nom de votre container, vous pouvez le retrouver avec la commande qui liste les containers existants :
> podman.exe ps -a

Exécutez les commandes suivantes :

> podman.exe stop {nom_du_container}

> podman.exe start {nom_du_container}

> podman.exe attach {nom_du_container} + Entrée

login : admin

password : pwd

Vous êtes maintenant dans votre environnement de travail.
Si vous avez oublié le nom de votre répertoire de travail partagé, vous pouvez le retrouver avec la commande :
> ls

Placez-vous dans votre répertoire partagé :
> cd {nom_de_votre_répertoire_partagé}

Vous devriez pouvoir lancer votre premier test !
> python3 main.py example_conf.json


# Utilisation :

Construisez votre fichier de configuration en vous basant sur le modèle (example_conf.json) et sur les schémas de description de scène présents en annexe (Est-Ouest.png ou Nord-Sud.png, selon l'orientation de vos rangées de panneaux).
Dans le container démarré, placez-vous dans le dossier où se trouvent les fichiers source (votre répertoire partagé, voir ci-dessus), puis utilisez cette commande :

> python3 main.py \<filename.json>

Remplacez filename.json par le nom de votre fichier de configuration. Si ce fichier est situé ailleurs que dans le dossier où sont les sources (ex : vous avez créé un sous-dossier "results"), préciser le chemin vers le fichier de configuration :

> python3 main.py \<results/filename.json>

Vous pouvez lancer le script, ou, si vous souhaitez utiliser une résolution personnalisée plutôt que celle par défault pour la carte, vous pouvez ajouter un argument -r [résolution souhaitée d'un pixel, en m]

> python3 main.py \<filename.json> -r 0.2

Ici, la résolution demandée est 0.2 m, ce qui signifie que les pixels de la carte auront une taille réelle approximative de 20 cm (ne pas se fier à cette mesure pour calculer des distances sur la carte, la résolution pouvant varier légèrement d'un pixel à l'autre).

Attendre la fin de l'exécution du script.



# Description des sorties :

#### filename.png :
Cette sortie correspond à la carte de rayonnement sur la période demandée.

#### filename_3d.png :
Cette sortie correspond à une projection 3D des panneaux sur la carte de rayonnement pour mieux se rendre compte de la position des panneaux au-dessus de la carte.

#### filename_calculs.json :
Cette sortie indique les taux de couverture du site expérimental selon deux formules différentes (Dupraz et la formule légale), apporte des précisions sur la localisation précise de la station météo d'où proviennent les données, et indique la distance en km entre la station et le point GPS du site expérimental.

#### filename_meteo.json :
Cette sortie sauvegarde les données météo utilisées pour la simulation (taux horaire de rayonnement diffus et direct).

#### filename_distribution.png :
Cette sortie permet de voir la distribution des couleurs de la carte de rayonnement sous forme d'un histogramme.