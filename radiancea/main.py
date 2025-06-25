
from flask import Flask, request, jsonify
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import requests

app = Flask(__name__)

OPENCAGE = "588600db369441e081e630f273fa680f"

SIGN_TO_RADIANCE = {
    "Bélier": "Renforcement", "Taureau": "Matérialisation", "Gémeaux": "Transmutation",
    "Cancer": "Manipulation", "Lion": "Émission", "Vierge": "Matérialisation",
    "Balance": "Manipulation", "Scorpion": "Spécialisation", "Sagittaire": "Émission",
    "Capricorne": "Renforcement", "Verseau": "Transmutation", "Poissons": "Spécialisation"
}

ZODIAC_SIGNS = [
    ("Capricorne", (12, 22), (1, 19)), ("Verseau", (1, 20), (2, 18)), ("Poissons", (2, 19), (3, 20)),
    ("Bélier", (3, 21), (4, 19)), ("Taureau", (4, 20), (5, 20)), ("Gémeaux", (5, 21), (6, 20)),
    ("Cancer", (6, 21), (7, 22)), ("Lion", (7, 23), (8, 22)), ("Vierge", (8, 23), (9, 22)),
    ("Balance", (9, 23), (10, 22)), ("Scorpion", (10, 23), (11, 21)), ("Sagittaire", (11, 22), (12, 21))
]

def get_coords(city):
    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={OPENCAGE}&limit=1"
        r = requests.get(url).json()
        geo = r["results"][0]["geometry"]
        return geo["lat"], geo["lng"]
    except:
        return 48.8566, 2.3522

def ascendant(jour, mois, annee, heure, ville):
    h, m = map(int, heure.split(":"))
    dt = Datetime(f"{annee}-{mois:02d}-{jour:02d} {h:02d}:{m:02d}:00", "UTC")
    lat, lon = get_coords(ville)
    chart = Chart(dt, GeoPos(str(lat), str(lon)))
    return chart.get("ASC").sign

def chemin_de_vie(j, m, a):
    total = sum(int(c) for c in f"{j:02d}{m:02d}{a}")
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(c) for c in str(total))
    return total

@app.route("/create_character", methods=["GET"])
def create_character():
    args = request.args
    nom = args.get("nom", "Inconnu")
    prenom = args.get("prenom", "Inconnu")
    ego = int(args.get("ego", 15))
    jour = int(args.get("jour", 1))
    mois = int(args.get("mois", 1))
    annee = int(args.get("annee", 2000))
    heure = args.get("heure", "12:00")
    lieu = args.get("lieu", "Paris")

    emoji = "🌑" if ego >= 30 else "⚫"
    marques = 2 if ego <= 5 or ego >= 25 else 1
    chemin = chemin_de_vie(jour, mois, annee)
    if chemin in [3, 6, 9, 11, 22, 33]:
        marques += 1

    zodiac = "Inconnu"
    for sign, start, end in ZODIAC_SIGNS:
        if (mois == start[0] and jour >= start[1]) or (mois == end[0] and jour <= end[1]):
            zodiac = sign
            break

    asc = ascendant(jour, mois, annee, heure, lieu)
    return jsonify({
        "nom": nom,
        "prenom": prenom,
        "ego": ego,
        "zodiaque": zodiac,
        "radiance": SIGN_TO_RADIANCE.get(zodiac, "Inconnue"),
        "ascendant": asc,
        "inhibition": SIGN_TO_RADIANCE.get(asc, "Inconnue"),
        "marques": marques,
        "numerologie": chemin
    })

app.run(host="0.0.0.0", port=81)
