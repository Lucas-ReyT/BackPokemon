from flask import Flask, jsonify, request
from db import collection, collection_users, type_collection
from flask_cors import CORS
import base64
from bson.binary import Binary
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict

app = Flask(__name__)
CORS(app)

#Route pour afficher les pokémons par "page"
#Ici, on affiche les 50 premiers pokémons



@app.route('/page/<int:page>', methods=['GET'])
def get_pokemon_by_page(page):
    limit = 50
    skip = (page - 1) * limit
    query = {'Name': {'$not': {'$regex': 'Mega '}}}

    pokemons = list(collection.find(query).skip(skip).limit(limit))

    results = []  

    for p in pokemons:
        p['_id'] = str(p['_id'])

        if 'Image' in p:
            image_binary = p['Image']
            try:
                if isinstance(image_binary, (Binary, bytes)):
                    p['Image'] = base64.b64encode(image_binary).decode('utf-8')
                else:
                    p['Image'] = None
            except Exception:
                p['Image'] = None

        results.append(p)

    return jsonify(results)


#Route pour afficher les pokémons en fonction du nom 


@app.route('/pokemon/<string:pokemon_name>', methods=['GET'])
def get_pokemon_by_name(pokemon_name):
    Check_Pokemon = collection.find_one({'Name': {'$regex': f'^{pokemon_name}$', '$options': 'i'}})

    if Check_Pokemon is None:
        return jsonify({'error': f"Le Pokémon '{pokemon_name}' n'a pas été trouvé."}), 404

    pokemon_types = Check_Pokemon.get('Type', [])
    type_combined = {}

    for t in pokemon_types:
        type_info = type_collection.find_one({'Type': t})
        if not type_info:
            continue
        for atk_type, multiplier in type_info.items():
            if isinstance(multiplier, (int, float)):
                if atk_type in type_combined:
                    type_combined[atk_type] *= multiplier
                else:
                    type_combined[atk_type] = multiplier

    faiblesses = {}
    tres_faible = {}
    resistances = {}
    tres_resistant = {}
    immunites = {}

    for atk_type, multiplier in type_combined.items():
        if multiplier > 2:
            tres_faible[atk_type] = multiplier
        elif multiplier > 1:
            faiblesses[atk_type] = multiplier
        elif multiplier == 0:
            immunites[atk_type] = multiplier
        elif multiplier < 0.5:
            tres_resistant[atk_type] = multiplier
        elif multiplier < 1:
            resistances[atk_type] = multiplier

    Check_Pokemon['_id'] = str(Check_Pokemon['_id'])

    Check_Pokemon['efficacite_type'] = {}
    if tres_faible:
        Check_Pokemon['efficacite_type']['tres_faible'] = tres_faible
    if faiblesses:
        Check_Pokemon['efficacite_type']['faiblesses'] = faiblesses
    if tres_resistant:
        Check_Pokemon['efficacite_type']['tres_resistant'] = tres_resistant
    if resistances:
        Check_Pokemon['efficacite_type']['resistances'] = resistances
    if immunites:
        Check_Pokemon['efficacite_type']['immunites'] = immunites

    # Ajout de l'image encodée si présente
    if 'Image' in Check_Pokemon:
        image_binary = Check_Pokemon['Image']
        try:
            if isinstance(image_binary, (Binary, bytes)):
                Check_Pokemon['Image'] = base64.b64encode(image_binary).decode('utf-8')
            else:
                Check_Pokemon['Image'] = None
        except Exception:
            Check_Pokemon['Image'] = None

    return jsonify(Check_Pokemon)

#Route pour afficher le type du pokémon


@app.route('/type/<string:type_name>', methods=['GET'])
def get_pokemon_by_type(type_name):
    pokemons = list(collection.find({'Type': type_name.capitalize()}))

    total_count = len(pokemons)
    type_combinations = defaultdict(int)

    for p in pokemons:
        types = p.get('Type', [])
        if isinstance(types, str):  
            types = [types]
        sorted_types = sorted(types)  
        type_key = " / ".join(sorted_types)
        type_combinations[type_key] += 1
    response = {
        'type_recherche': type_name.capitalize(),
        'nombre_total': total_count,
        'combinaisons': dict(type_combinations)
    }

    return jsonify(response)

#Par type et par stat


@app.route('/filtre', methods=['GET'])
def get_filtered_pokemons():
    type_filter = request.args.get('type', default=None, type=str)
    min_total = request.args.get('min_total', default=0, type=int)

    stats_keys = [
        'HP Base', 'Attack Base', 'Defense Base',
        'Special Attack Base', 'Special Defense Base', 'Speed Base'
    ]

    query = {}
    if type_filter:
        query['Type'] = type_filter.capitalize()

    pokemons = collection.find(query)
    filtered = []

    for p in pokemons:
        try:
            total = sum(int(p.get(stat, 0)) for stat in stats_keys)
        except ValueError:
            continue

        if total >= min_total:
            p['_id'] = str(p['_id'])
            p['Total Base Stat'] = total
            
            if 'Image' in p:
                image_binary = p['Image']
                try:
                    if isinstance(image_binary, (Binary, bytes)):
                        p['Image'] = base64.b64encode(image_binary).decode('utf-8')
                    else:
                        p['Image'] = None
                except Exception:
                    p['Image'] = None

            filtered.append(p)

    return jsonify({
        'type': type_filter,
        'min_total': min_total,
        'nombre_resultats': len(filtered),
        'pokemons': filtered
    })

#Route qui affiche le total des types
@app.route('/tottype', methods=['GET'])
def get_all_types():
    all_pokemons = collection.find()
    unique_types = set()

    for p in all_pokemons:
        types = p.get('Type', [])
        if isinstance(types, str):  
            types = [types]
        for t in types:
            unique_types.add(t.capitalize())

    return jsonify(sorted(list(unique_types)))



# créer un User
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if collection_users.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)

    collection_users.insert_one({
        'username': username,
        'password': hashed_password,
        'team': []
    })

    return jsonify({'message': f'User {username} created successfully'})

#Créer une équipe 
@app.route('/user/<username>/add', methods=['POST'])
def toggle_pokemon_in_team(username):
    data = request.json
    pokemon_name = data.get('pokemon')

    user = collection_users.find_one({'username': username})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    team = user.get('team', [])

    if pokemon_name in team:
        collection_users.update_one(
            {'username': username},
            {'$pull': {'team': pokemon_name}}
        )
        return jsonify({'message': f'{pokemon_name} removed from {username}\'s team'})
    if len(team) >= 6:
        return jsonify({'error': 'Team already has 6 Pokémon'}), 400

    collection_users.update_one(
        {'username': username},
        {'$push': {'team': pokemon_name}}
    )
    return jsonify({'message': f'{pokemon_name} added to {username}\'s team'})


#Afficher l'user et son équipe 
@app.route('/user/<username>', methods=['GET'])
def get_user(username):
    user = collection_users.find_one({'username': username})
    if user:
        return jsonify({
            'username': user['username'],
            'team': user['team'],
        })
    else:
        return jsonify({'error': 'User not found'}), 404


#Route pour chercher les pokémons par statistiques 
@app.route('/statistiques', methods=['GET'])
def get_pokemons_by_stats():
    min_total = request.args.get('min_total', default=0, type=int)

    stats_keys = [
        'HP Base', 'Attack Base', 'Defense Base',
        'Special Attack Base', 'Special Defense Base', 'Speed Base'
    ]

    filtered_pokemons = []
    all_pokemons = collection.find()  

    for p in all_pokemons:
        try:
            total = sum(int(p.get(stat, 0)) for stat in stats_keys)
        except ValueError:
            continue  

        if total >= min_total:
            p['_id'] = str(p['_id'])  #
            p['Total Base Stat'] = total
            filtered_pokemons.append(p)

    return jsonify(filtered_pokemons)

    
#Se connecter à son compte
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = collection_users.find_one({'username': username})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({'error': 'Incorrect password'}), 401

    return jsonify({'message': f'Connexion de {username}'})

if __name__ == '__main__':
    app.run(debug=True)
