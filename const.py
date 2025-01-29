# custom_components/hmemorial/const.py

"""Constantes pour hmemorial."""
DOMAIN = "hmemorial"

# Clés de configuration
CONF_LOCATION = "location"
CONF_ELEVATION = "elevation"
CONF_TIME_ZONE = "time_zone"

# Valeurs par défaut
DEFAULT_NAME = "HMemorial"
DEFAULT_LANGUAGE = "english"

# Intervalles de mise à jour (en secondes)
DEFAULT_SCAN_INTERVAL = 600

# Autres constantes
ATTRIBUTION = "Data provided by HMemorial"

# Fichier de données
FILE_PATH_MEMORIAL = "custom_components/hmemorial/data_memorial.txt"
FILE_PATH_BIRTHDAY = "custom_components/hmemorial/data_birthday.txt"

# Schéma des options
import voluptuous as vol

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("option1", default=True): bool,
        vol.Optional("option2", default="default_value"): str,
    }
)
