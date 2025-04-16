from flask import Flask, jsonify, request
from db import collection, collection_users
from flask_cors import CORS

app = Flask(__name__)

#Route pour afficher les pokémons par "page"
#Ici, on affiche les 50 premiers pokémons

CORS(app)

@app.route('/page/<int:page>', methods=['GET'])
def get_pokemon_by_page(page):
    limit = 50
    skip = (page - 1) * limit
    pokemons = list(collection.find().skip(skip).limit(limit))
    
    for p in pokemons:
        p['_id'] = str(p['_id'])
    
    return jsonify(pokemons)


#Route pour afficher les pokémons en fonction du nom 
@app.route('/pokemon/<string:pokemon_name>', methods=['GET'])
def get_pokemon_by_name(pokemon_name):
    pokemon = collection.find_one({'Name': {'$regex': f'^{pokemon_name}$', '$options': 'i'}})
    
    if pokemon:
        pokemon['_id'] = str(pokemon['_id'])
        return jsonify(pokemon)
    else:
        return jsonify({'error': 'Pokemon not found'}), 404
    
#Route pour afficher le type du pokémon
@app.route('/type/<string:type_name>', methods=['GET'])
def get_pokemon_by_type(type_name):
    
    pokemons = list(collection.find({'Type': {'$regex': f'.*{type_name}.*', '$options': 'i'}}))
    
    for p in pokemons:
        p['_id'] = str(p['_id'])
    
    if pokemons:
        return jsonify(pokemons)
    else:
        return jsonify({'error': f'No Pokémon found with type {type_name}'}), 404





# créer un User
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    # Vérifie si le pseudo existe déjà
    if collection_users.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400
    
    collection_users.insert_one({'username': username, 'team': []})
    return jsonify({'message': f'User {username} created successfully'})

#Créer une équipe 
@app.route('/user/<username>/add', methods=['POST'])
def add_pokemon_to_team(username):
    data = request.json
    pokemon_name = data.get('pokemon')

    user = collection_users.find_one({'username': username})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if len(user['team']) >= 6:
        return jsonify({'error': 'Team already has 6 Pokémon'}), 400

    if pokemon_name in user['team']:
        return jsonify({'error': 'Pokémon already in team'}), 400

    collection_users.update_one(
        {'username': username},
        {'$push': {'team': pokemon_name}}
    )
    return jsonify({'message': f'{pokemon_name} added to {username}\'s team'})

if __name__ == '__main__':
    app.run(debug=True)
