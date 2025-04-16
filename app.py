from flask import Flask, jsonify
from db import collection

app = Flask(__name__)

#Route pour afficher les pokémons par "page"
#Ici, on affiche les 50 premiers pokémons
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



if __name__ == '__main__':
    app.run(debug=True)
