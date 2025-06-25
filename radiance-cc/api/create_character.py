
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import requests
import hashlib
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# Clé API pour OpenCage
OPENCAGE_API_KEY = "588600db369441e081e630f273fa680f"

# Zodiac + Radiance
ZODIAC_SIGNS = [
    ("Capricorne", (12, 22), (1, 19), "Renforcement"),
    ("Verseau", (1, 20), (2, 18), "Transmutation"),
    ("Poissons", (2, 19), (3, 20), "Projection"),
    ("Bélier", (3, 21), (4, 19), "Conjuration"),
    ("Taureau", (4, 20), (5, 20), "Matérialisation"),
    ("Gémeaux", (5, 21), (6, 20), "Manipulation"),
    ("Cancer", (6, 21), (7, 22), "Conjuration"),
    ("Lion", (7, 23), (8, 22), "Renforcement"),
    ("Vierge", (8, 23), (9, 22), "Matérialisation"),
    ("Balance", (9, 23), (10, 22), "Manipulation"),
    ("Scorpion", (10, 23), (11, 21), "Projection"),
    ("Sagittaire", (11, 22), (12, 21), "Transmutation")
]

SEPHIROTH_BY_MONTH = {
    1: "Binah", 2: "Chokhmah", 3: "Hesed", 4: "Guevourah",
    5: "Hod", 6: "Netzah", 7: "Yesod", 8: "Daath",
    9: "Tiferet", 10: "Geburah", 11: "Kether", 12: "Malkuth"
}

EFFECTS_MARQUES = {
    1: "Pouvoir mineur",
    2: "Pouvoir médian",
    3: "Pouvoir élémentaire",
    4: "Force de la Terre",
    5: "Vision sur les âmes",
    6: "Porteur du chaos"
}

def get_coords_from_city(city):
    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={OPENCAGE_API_KEY}&limit=1"
        response = requests.get(url)
        data = response.json()
        if data["results"]:
            geometry = data["results"][0]["geometry"]
            return geometry["lat"], geometry["lng"]
    except:
        pass
    return 48.8566, 2.3522  # fallback : Paris

def real_ascendant(jour, mois, heure_str, lieu="Paris"):
    try:
        lat, lon = get_coords_from_city(lieu)
        heure, minute = map(int, heure_str.split(":"))
        date_str = f"{annee}-{mois:02d}-{jour:02d}"  # année fictive
        dt = Datetime(f"{date_str} {heure:02d}:{minute:02d}:00", "UTC")
        pos = GeoPos(str(lat), str(lon))
        chart = Chart(dt, pos)
        return chart.get("ASC").sign
    except:
        return "Inconnu"

def couleur_ego_complet(ego):
    table = {
        1:  ("🤍", "#FFFFFF"),  2: ("🤍", "#F8F8F8"),  3: ("⚪", "#EEEEEE"),
        4:  ("⚪", "#DDDDDD"),  5: ("⚫", "#BBBBBB"),  6: ("⚫", "#999999"),
        7:  ("🖤", "#444444"),  8: ("🖤", "#222244"),  9: ("🟥", "#550033"),
        10: ("🟥", "#660022"), 11: ("🟥", "#770033"), 12: ("🔴", "#880000"),
        13: ("🔴", "#AA0000"), 14: ("🔴", "#FF3300"), 15: ("🧡", "#FF6600"),
        16: ("🟠", "#FF9900"), 17: ("🟡", "#FFD700"), 18: ("🟨", "#CCFF66"),
        19: ("🟩", "#66FFCC"), 20: ("🟦", "#00FFFF"), 21: ("🔵", "#00CCCC"),
        22: ("🟢", "#00AA99"), 23: ("🟢", "#007755"), 24: ("🟢", "#005522"),
        25: ("🔵", "#0033AA"), 26: ("🔵", "#001177"), 27: ("🟣", "#220044"),
        28: ("🟤", "#331122"), 29: ("⚫", "#111111"), 30: ("🌑", "#000000")
    }
    return table.get(ego, ("❔", "#777777"))


def chemin_de_vie(jour, mois, annee):
    total = sum(int(c) for c in f"{jour:02d}{mois:02d}{annee}")
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(c) for c in str(total))
    return total



def valider_entrees(ego, jour, mois, annee, heure):
    if not (1 <= ego <= 30):
        return False, "L'ego doit être entre 1 et 30."
    if not (1 <= jour <= 31):
        return False, "Le jour doit être entre 1 et 31."
    if not (1 <= mois <= 12):
        return False, "Le mois doit être entre 1 et 12."
    if not (1900 <= annee <= 2100):
        return False, "L'année doit être entre 1900 et 2100."
    try:
        h, m = map(int, heure.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return False, "Heure invalide."
    except:
        return False, "Format d'heure incorrect. Attendu HH:MM."
    return True, ""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        nom = query.get("nom", ["Inconnu"])[0]
        prenom = query.get("prenom", ["Inconnu"])[0]
        ego = int(query.get("ego", [15])[0])
        jour = int(query.get("jour", [1])[0])
        mois = int(query.get("mois", [1])[0])
        annee = int(query.get("annee", [2000])[0])
        heure = query.get("heure", ["12:00"])[0]
        lieu = query.get("lieu", ["Paris"])[0]
        valide, erreur = valider_entrees(ego, jour, mois, annee, heure)
        if not valide:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"erreur": erreur}).encode())
            return


        emoji, hex_color = couleur_ego_complet(ego)
        marques = 2 if ego <= 5 or ego >= 25 else 1
        if ego in [11, 22]:
            marques += 1

        zodiac = "Inconnu"
        radiance = "Inconnue"
        for sign, start, end, rad in ZODIAC_SIGNS:
            if (mois == start[0] and jour >= start[1]) or (mois == end[0] and jour <= end[1]):
                zodiac = sign
                radiance = rad
                break

        sephiroth = SEPHIROTH_BY_MONTH.get(mois, "Aucune")
        chemin = chemin_de_vie(jour, mois, annee)
        if chemin in [3, 6, 9, 11, 22, 33]:
            marques += 1

        ascendant = real_ascendant(jour, mois, heure, lieu)
        inhibition = "Inconnue"
        for sign, _, _, rad in ZODIAC_SIGNS:
            if ascendant == sign:
                inhibition = rad
                break


        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "nom": nom,
            "prenom": prenom,
            "ego": ego,
            "couleur": emoji,
            "codeCouleur": hex_color,
            "zodiaque": zodiac,
            "radiance": radiance,
            "ascendant": ascendant,
            "sephiroth": sephiroth,
            "inhibition": inhibition,
            "marques": marques,
            "numerologie": chemin
        }, ensure_ascii=False).encode())
