# materials_utils.py

def create_lookup_table():
    return {
        'webcam': [('Plastic', 45), ('Glass', 25), ('Metal', 20), ('Silicon', 10)],
        'speakers': [('Plastic', 35), ('Metal', 30), ('Magnets', 20), ('Rubber', 15)],
        'ram': [('Silicon', 35), ('Fiberglass', 25), ('Plastic', 25), ('Metal', 15)],
        'mouse': [('Plastic', 50), ('Circuit Board', 25), ('Metal', 15), ('Rubber', 10)],
        'motherboard': [('Fiberglass', 35), ('Copper', 25), ('Plastic', 25), ('Silicon', 15)],
        'monitor': [('Glass', 40), ('Plastic', 30), ('Metal', 20), ('Liquid Crystal', 10)],
        'microphone': [('Plastic', 40), ('Metal', 30), ('Electronics', 20), ('Rubber', 10)],
        'laptop': [('Aluminium', 30), ('Plastic', 25), ('Copper', 20), ('Glass', 15), ('Silicon', 10)],
        'keyboard': [('Plastic', 45), ('Electronics', 25), ('Metal', 20), ('Rubber', 10)],
        'headset': [('Plastic', 35), ('Metal', 20), ('Electronics', 20), ('Foam', 15), ('Rubber', 10)],
        'hdd': [('Aluminium', 35), ('Electronics', 25), ('Magnetic Material', 25), ('Glass', 15)],
        'hard_drive': [('Aluminium', 35), ('Electronics', 25), ('Magnetic Material', 25), ('Glass', 15)],
        'gpu': [('Silicon', 35), ('Copper', 25), ('Aluminium', 25), ('Plastic', 15)],
        'cpu_coolers': [('Aluminium', 40), ('Copper', 30), ('Fan Blades', 20), ('Plastic', 10)],
        'cpu': [('Silicon', 40), ('Copper', 25), ('Aluminium', 20), ('Gold', 15)],
        'case': [('Steel', 40), ('Aluminium', 30), ('Plastic', 20), ('Glass', 10)],
        'cables': [('Copper', 50), ('Plastic', 35), ('Rubber', 15)],
        'battery': [('Lithium', 30), ('Metal Casing', 25), ('Cobalt', 25), ('Graphite', 20)]
    }

hazard_levels = {
    'Plastic': 40, 'Glass': 10, 'Metal': 30, 'Silicon': 20, 'Liquid Crystal': 50,
    'Electronics': 60, 'Aluminium': 20, 'Copper': 25, 'Gold': 15, 'Steel': 30,
    'Foam': 5, 'Rubber': 20, 'Lithium': 80, 'Cobalt': 90, 'Graphite': 15,
    'Magnetic Material': 35, 'Metal Casing': 30, 'Fan Blades': 10, 'Circuit Board': 50,
    'Fiberglass': 25, 'Magnets': 40
}

def get_component_materials(component_name, lookup_table=None):
    """
    component_name: predicted component like 'battery' or 'motherboard'
    returns: dict with 'component', 'materials' (list of "Name (X%)"), and 'hazard' (weighted %)
    """
    if lookup_table is None:
        lookup_table = create_lookup_table()

    key = component_name.lower().strip().replace(" ", "_")

    if key not in lookup_table:
        return {"component": component_name, "materials": [], "hazard": 0}

    materials = lookup_table[key]
    hazard_score = 0.0
    for mat, pct in materials:
        mat_hazard = hazard_levels.get(mat, 0)
        hazard_score += (pct * mat_hazard) / 100.0

    materials_formatted = [f"{m} ({p}%)" for m, p in materials]
    return {"component": component_name, "materials": materials_formatted, "hazard": round(hazard_score, 2)}
