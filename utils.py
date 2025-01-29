"""Fonctions utilitaires pour hmemorial,
   avec deux fichiers distincts : data_memorial.txt et data_birthday.txt.
"""

import datetime as dt
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import hdate
from hdate import HebrewDate
from homeassistant.core import HomeAssistant

from .const import FILE_PATH_BIRTHDAY, FILE_PATH_MEMORIAL

_LOGGER = logging.getLogger(__name__)


#
# 1) MEMORIAL - Fichier "data_memorial.txt"
#


def _sync_read_data_memorial(file_path: Path) -> list[dict]:
    """
    Fonction synchrone qui lit le fichier data_memorial.txt (décès).
    Cette fonction est exécutée dans un thread séparé via async_add_executor_job.
    """
    data_memorial = []

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
                    hdn = HebrewDate(year=year, month=month, day=day)
                    gdate = hdn.to_gdate()

                    # Log du type de gdate
                    _LOGGER.debug(
                        "Parsed Memorial - Name: %s, Gregorian Date: %s, Type: %s",
                        name,
                        gdate,
                        type(gdate),
                    )

                    # Vérifie que gdate est bien un datetime.date
                    if not isinstance(gdate, dt.date):
                        _LOGGER.error(
                            "Conversion error: gdate is not datetime.date for line: %s",
                            line,
                        )
                        continue

                    data_memorial.append(
                        {
                            "name": name,
                            "date": gdate,  # la date grégorienne
                            "type": "memorial",  # identifiant pour la suite
                            "hdate_original": hdn,  # si besoin d'un usage ultérieur
                        }
                    )

                except (ValueError, TypeError) as e:
                    _LOGGER.error(
                        "Impossible de parser la date hébraïque (ligne: %s) : %s",
                        line,
                        e,
                    )

    except Exception as e:
        _LOGGER.error("Erreur de lecture du fichier %s : %s", file_path, e)

    return data_memorial


async def read_data_memorial(hass: HomeAssistant) -> list[dict]:
    """
    Fonction asynchrone (appelée dans du code async) :
    - Appelle _sync_read_data_memorial en dehors de la boucle événementielle
      via async_add_executor_job.
    """
    file_path = Path(hass.config.path(FILE_PATH_MEMORIAL))
    return await hass.async_add_executor_job(_sync_read_data_memorial, file_path)


#
# 2) BIRTHDAY - Fichier "data_birthday.txt"
#


def _sync_read_data_birthday(file_path: Path) -> list[dict]:
    """
    Fonction synchrone qui lit le fichier data_birthday.txt (anniversaires).
    Exécutée dans un thread séparé.
    """
    data_birthday = []

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
                    data_birthday.append(
                        {
                            "name": name,
                            "date": gdate,
                            "type": "birthday",
                        }
                    )
                except ValueError as e:
                    _LOGGER.error(
                        "Impossible de parser la date grégorienne (ligne: %s) : %s",
                        line,
                        e,
                    )

    except Exception as e:
        _LOGGER.error("Erreur de lecture du fichier %s : %s", file_path, e)

    return data_birthday


async def read_data_birthday(hass: HomeAssistant) -> list[dict]:
    """
    Fonction asynchrone (appelée dans du code async) :
    - Appelle _sync_read_data_birthday en dehors de la boucle événementielle
      via async_add_executor_job.
    """
    file_path = Path(hass.config.path(FILE_PATH_BIRTHDAY))
    return await hass.async_add_executor_job(_sync_read_data_birthday, file_path)
