# Pour l'affichage de la carte
## Solution retenue : Matplotlib
### Avantages :
C'est une librairie Python, et le reste du code étant aussi en Python ce choix permettait d'éviter de panacher les languages pour ne pas complexifier le code. Après comparaison, il n'existe a pas d'autre librairie graphique aussi complète en Python.

Les graphes générés sont de bonne qualité.

### Inconvénients :
La documentation est mal faite, il vaut mieux s'appuyer sur des forums (Stackoverflow etc).

La génération d'un graphe à la géométrie un peu complexe est très lente.

# Pour la récupération des données météo
## Solution retenue : OpenMétéo
### Avantages :
Après avoir comparé avec d'autres sites météo, son API est très simple d'utilisation (pas besoin de clé API), offre un très bon maillage des stations (ce qui n'est pas le cas de Climatik) et renvoie toujours les variables demandées (ce qui n'est pas le cas de Météo France, qui renvoie parfois des CSV à moitié vides). De plus, le nombre d'appels gratuits par jour est largement suffisant pour ce cas d'usage (10000).
### Inconvénients :
La précision des données semble moindre que sur Climatik

# Pour la modélisation de l'éclairement
## Solution retenue : Caribu
### Avantages :
C'est un modèle développé par l'INRA que l'on sait fiable.

Le modèle formalise bien les sources d'éclairement et permet de rendre compte de la position du soleil à chaque pas de temps.

### Inconvénient :
Absence de documentations d'installation et d'utilisation

Le modèle est intégré dans tout un environnement openalea nécessaire à son utilisation, même en usage sans autre dépendance.

Le calcul de rayonnement est lent, même avec une scène géométrique simple.

# Pour l'environnement du projet
## Solution retenue : Conteneurisation (avec WSL2 et Podman)
### Avantages :
Cette solution permet de scripter l'installation, qui est complexe et nécessite de nombreuses dépendances à cause de Caribu. Cela permet une meilleure portabilité du code.
La conteneurisation permet également de supprimer facilement le projet et ses dépendances et de repartir d'une base neuve en cas de souci avec une librairie, sans devoir désinstaller manuellement toutes les dépendances de sa machine personnelle.