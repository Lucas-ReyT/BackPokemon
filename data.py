#--  Installation des bibliothèques
import os
import shutil
!pip install Kaggle
from kaggle.api.kaggle_api_extended import KaggleApi
import json
from pymongo import MongoClient



# Définir manuellement les variables d'environnement
os.environ['KAGGLE_USERNAME'] = 'thomasalmodovar'
os.environ['KAGGLE_KEY'] = 'f1467a49c43e898418f52863f70b31d1'

# Initialisation de l'API
api = KaggleApi()
api.authenticate()

# Spécifie l'ID du dataset
dataset = 'divyanshusingh369/complete-pokemon-library-32k-images-and-csv'

# Chemin de téléchargement
download_path = './'  # Remplace par le chemin voulu

# Télécharger tout le dataset
api.dataset_download_files(dataset, path=download_path, unzip=True)

print("Téléchargement terminé!", )





# --- CONFIG ---
MONGO_URI = "mongodb+srv://MP-Death30:1234@cluster0.dtgdmge.mongodb.net/myDatabase?retryWrites=true&w=majority"
DB_NAME = "Pokemon"
COLLECTION_NAME = "Pokemon_collection"
IMAGE_FOLDER = "./Pokemon Images DB/Pokemon Images DB"  # Dossier racine contenant les images

def supprimer_parentheses_dans_chemin(chemin):
    for element in os.listdir(chemin):
        chemin_element = os.path.join(chemin, element)
        if os.path.isdir(chemin_element):
            # Si l'élément est un dossier, on le traite
            nouveau_nom = element.replace('(', '').replace(')', '')
            if nouveau_nom != element:
                # Si le nom change, on renomme le dossier
                nouveau_chemin = os.path.join(chemin, nouveau_nom)
                if os.path.exists(nouveau_chemin):
                    # Si le nouveau chemin existe déjà, on gère la situation
                    print(f"Erreur : Le dossier '{nouveau_chemin}' existe déjà. Impossible de renommer '{chemin_element}'.")
                    # Vous pouvez soit lever une exception, soit essayer de fusionner les contenus, soit autre chose...
                else:
                    os.rename(chemin_element, nouveau_chemin)
                    print(f"Renommé '{chemin_element}' en '{nouveau_chemin}'")
                    # On continue avec le chemin mis à jour
                    supprimer_parentheses_dans_chemin(nouveau_chemin)
            else:
                pass
                # Si le nom ne change pas, on continue simplement avec le sous-dossier
                
supprimer_parentheses_dans_chemin(IMAGE_FOLDER)

# --- Chargement du JSON ---
with open('pokemonDB_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# --- Trouver les images se terminant par "_new" ---
def find_pokemon_image_folder(pokemon_name):
    """Retourne le chemin absolu de l'image se terminant par '_new' pour un Pokémon donné."""
    pokemon_folder = os.path.join(IMAGE_FOLDER, pokemon_name)
    pokemon_folder = pokemon_folder.replace("\\","/")
    if not os.path.exists(pokemon_folder):
        return None

    # Chercher les fichiers dans le dossier du Pokémon
    for file_name in os.listdir(pokemon_folder):
        if file_name.endswith("_new.png") or file_name.endswith("_new.jpg"):
            return os.path.join(pokemon_folder, file_name).replace("\\","/")
    return None

# --- Mise en forme des données pour intégration dans Mongo ---
converted = []

for name, attributes in data.items():
    entry = {'Name': name}
    
    for key, value in attributes.items():
        if key in ["Type", "Egg Groups"]:
            entry[key] = [item.strip() for item in value.split(',')]
        else:
            entry[key] = value

    # Ajout de l'image si elle existe
    image_path = find_pokemon_image_folder(name)
    print(image_path)
    if image_path:  # Si une image "_new" est trouvée
        with open(image_path, "rb") as img_file:
            entry['Image'] = img_file.read()  # Stocker les données en binaire
            

    converted.append(entry)

# --- Envoyer les données sur MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Efface les données si elles existent et les remplace
collection.delete_many({})
collection.insert_many(converted)

print(f"{len(converted)} documents (pokémons) mis à jour dans {DB_NAME}.{COLLECTION_NAME}")