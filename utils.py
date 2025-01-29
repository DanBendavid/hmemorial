"""Fonctions utilitaires pour hmemorial,
   avec deux fichiers distincts : data_memorial.txt et data_birthday.txt.
"""

import logging
from pathlib import Path
import datetime as dt


from homeassistant.core import HomeAssistant

from .lib.hdate import HebrewDate, HDate
from .const import FILE_PATH_MEMORIAL, FILE_PATH_BIRTHDAY

_LOGGER = logging.getLogger(__name__)

def read_data_memorial(hass: HomeAssistant):
    """
    Lire le fichier data_memorial.txt qui contient uniquement les décès (dates hébraïques).
    Format par ligne: name, month, day, year
    Exemple:
      David, 5, 10, 5783
    
    Retourne une liste de dictionnaires:
    [
      {
        "name": ...,
        "date": <date grégorienne (datetime.date)>,
        "type": "memorial",
        "hdate_original": <HebrewDate (optionnel pour plus tard)>,
      },
      ...
    ]
    """
    data_memorial = []
    file_path = Path(hass.config.path(FILE_PATH_MEMORIAL))
    if not file_path.exists():
        _LOGGER.error("Fichier %s non trouvé", file_path)
        return data_memorial

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                # On s'attend à 4 colonnes : name, month, day, year
                if len(parts) < 4:
                    _LOGGER.error("Ligne invalide (4 champs requis) : %s", line)
                    continue

                name = parts[0].strip()
                try:
                    month = int(parts[1].strip())
                    day = int(parts[2].strip())
                    year = int(parts[3].strip())

                    # On crée un HebrewDate
                    hdate_obj = HebrewDate(year=year, month=month, day=day)
                    hdate_instance = HDate(hdate_obj)
                    gdate = hdate_instance.gdate

                    # Log the type of gdate
                    _LOGGER.debug(
                        "Parsed Memorial - Name: %s, Gregorian Date: %s, Type: %s",
                        name, gdate, type(gdate)
                    )

                    # Ensure gdate is datetime.date
                    if not isinstance(gdate, dt.date):
                        _LOGGER.error(
                            "Conversion error: gdate is not datetime.date for line: %s", line
                        )
                        continue

                    data_memorial.append({
                        "name": name,
                        "date": gdate,           # la date grégorienne
                        "type": "memorial",      # identifiant pour la suite
                        "hdate_original": hdate_obj,  # si besoin d'un usage ultérieur
                    })

                except (ValueError, TypeError) as e:
                    _LOGGER.error(
                        "Impossible de parser la date hébraïque (ligne: %s) : %s", line, e
                    )

    except Exception as e:
        _LOGGER.error("Erreur de lecture du fichier %s : %s", file_path, e)

    return data_memorial


def read_data_birthday(hass: HomeAssistant):
    """
    Lire le fichier data_birthday.txt qui contient uniquement les anniversaires (dates grégoriennes).
    Format par ligne : name, YYYY-MM-DD
    Exemple:
      Laura, 1985-02-25

    Retourne une liste de dictionnaires:
    [
      {
        "name": ...,
        "date": <date grégorienne (datetime.date)>,
        "type": "birthday",
      },
      ...
    ]
    """
    data_birthday = []
    file_path = Path(hass.config.path(FILE_PATH_BIRTHDAY))
    if not file_path.exists():
        _LOGGER.error("Fichier %s non trouvé", file_path)
        return data_birthday

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                # On s'attend à 2 colonnes : name, YYYY-MM-DD
                if len(parts) < 2:
                    _LOGGER.error("Ligne invalide (2 champs requis) : %s", line)
                    continue

                name = parts[0].strip()
                date_str = parts[1].strip()

                try:
                    gdate = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
                    data_birthday.append({
                        "name": name,
                        "date": gdate,
                        "type": "birthday",
                    })
                except ValueError as e:
                    _LOGGER.error(
                        "Impossible de parser la date grégorienne (ligne: %s) : %s", line, e
                    )

    except Exception as e:
        _LOGGER.error("Erreur de lecture du fichier %s : %s", file_path, e)

    return data_birthday
