from flask import Flask, jsonify
from db import collection

app = Flask(__name__)

@app.route('/pokemon<int:page>', methods=['GET'])
def get_pokemon_by_page(page):
    limit = 50
    skip = (page - 1) * limit
    pokemons = list(collection.find().skip(skip).limit(limit))
    
    for p in pokemons:
        p['_id'] = str(p['_id'])
    
    return jsonify(pokemons)

@app.route('/nom<string:pokemon_name>', methods=['GET'])
def get_pokemon_by_name(pokemon_name):
    pokemon = collection.find_one({'Name': {'$regex': f'^{pokemon_name}$', '$options': 'i'}})
    
    if pokemon:
        pokemon['_id'] = str(pokemon['_id'])
        return jsonify(pokemon)
    else:
        return jsonify({'error': 'Pokemon not found'}), 404



if __name__ == '__main__':
    app.run(debug=True)
