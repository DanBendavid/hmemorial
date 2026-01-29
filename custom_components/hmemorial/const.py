# custom_components/hmemorial/const.py
import json
from pathlib import Path

"""Constantes pour hmemorial."""
# Valeurs par défaut
DOMAIN = "hmemorial"
DEFAULT_NAME = "HMemorial"

# Clés de configuration
CONF_LOCATION = "location"
CONF_ELEVATION = "elevation"
CONF_TIME_ZONE = "time_zone"
CONF_DIASPORA = "diaspora"
CONF_LANGUAGE = "language"
CONF_TRADITION = "tradition"
CONF_PRAYER_ONLY = "prayer_only"
CONF_ENABLE_MEMORIAL = "enable_memorial"
CONF_ENABLE_BIRTHDAY = "enable_birthday"
CONF_ALTITUDE = "altitude"  # The name used by the hdate library for elevation

CONF_CANDLE_LIGHT_MINUTES = "candle_lighting_minutes_before_sunset"
CONF_HAVDALAH_OFFSET_MINUTES = "havdalah_minutes_after_sunset"
DEFAULT_HAVDALAH_OFFSET_MINUTES = 0
DEFAULT_CANDLE_LIGHT = 18

DEFAULT_LANGUAGE = "en"
DEFAULT_DIASPORA = True
DEFAULT_TRADITION = "ashkenazi"
DEFAULT_ENABLE_MEMORIAL = True
DEFAULT_ENABLE_BIRTHDAY = True
# Clés de configuration pour les options
# Intervalles de mise à jour (en secondes)
DEFAULT_SCAN_INTERVAL = 60

# Autres constantes
ATTRIBUTION = "Data provided by HMemorial"
DEFAULT_ATTRIBUTION = "Données issues de hdate"

# Fichier de données
FILE_PATH_MEMORIAL = "custom_components/hmemorial/data_memorial.txt"
FILE_PATH_BIRTHDAY = "custom_components/hmemorial/data_birthday.txt"

# Nusachim supportés
NUSACHIM = ["ashkenazi", "sephardi"]

# Langues supportées
LANGUAGES = ["he", "fr", "en"]


# Charger les icônes au démarrage du module
def load_static_icons():
    try:
        icon_file = Path(__file__).parent / "icons.json"
        with open(icon_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


ICONS_MAPPING = load_static_icons()

# Icônes par défaut si le fichier n'est pas trouvé
DEFAULT_ICONS = {
    "memorial": "mdi:candle",
    "birthday": "mdi:cake-variant",
    "zmanim": "mdi:clock-outline",
    "shabbat": "mdi:star-david",
}
