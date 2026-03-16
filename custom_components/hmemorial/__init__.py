"""Initialisation du composant hmemorial."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from hdate import Location
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_TIME_ZONE,
    Platform,
)
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CANDLE_LIGHT_MINUTES,
    CONF_DIASPORA,
    CONF_HAVDALAH_OFFSET_MINUTES,
    DEFAULT_CANDLE_LIGHT,
    DEFAULT_DIASPORA,
    DEFAULT_HAVDALAH_OFFSET_MINUTES,
    DEFAULT_LANGUAGE,
    DOMAIN,
)
from .coordinator import HmemorialDataUpdateCoordinator
from .entity import HmemorialData  # ou Hmemorialdata selon le nom correct

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor"]  # Plates-formes gérées
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_FRONTEND_URL = "/hmemorial/hmemorial-card.js"
_FRONTEND_FILE = Path(__file__).parent / "frontend" / "hmemorial-card.js"
_COMMUNITY_CARD_DIR = Path("www") / "community" / "hmemorial-card"
_COMMUNITY_CARD_FILE = "hmemorial-card.js"


@dataclass(frozen=True)
class _StaticPath:
    url_path: str
    path: str
    cache_headers: bool = False


def _register_frontend(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("_frontend_registered"):
        return
    if hasattr(hass.http, "register_static_path"):
        hass.http.register_static_path(
            _FRONTEND_URL,
            str(_FRONTEND_FILE),
            cache_headers=False,
        )
    elif hasattr(hass.http, "async_register_static_paths"):
        hass.http.async_register_static_paths(
            [_StaticPath(_FRONTEND_URL, str(_FRONTEND_FILE), cache_headers=False)]
        )
    else:
        _LOGGER.warning("HTTP static path registration is not supported.")
    data["_frontend_registered"] = True


def _ensure_community_card(hass: HomeAssistant) -> None:
    target_dir = Path(hass.config.path(str(_COMMUNITY_CARD_DIR)))
    target_file = target_dir / _COMMUNITY_CARD_FILE
    source_file = _FRONTEND_FILE

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        if target_file.exists():
            same_size = target_file.stat().st_size == source_file.stat().st_size
            if same_size and target_file.stat().st_mtime >= source_file.stat().st_mtime:
                return
        shutil.copyfile(source_file, target_file)
    except Exception as err:
        _LOGGER.warning("Unable to copy frontend card to %s: %s", target_file, err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initialisation du composant."""
    _LOGGER.debug("Initialisation du composant hmemorial")
    _register_frontend(hass)
    await hass.async_add_executor_job(_ensure_community_card, hass)
    await hass.async_add_executor_job(_ensure_community_card, hass)
    return True



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer hmemorial à partir d'une entrée de configuration."""
    _register_frontend(hass)
    _LOGGER.info("Configuration de l'entrée hmemorial : %s", entry.entry_id)

    conf = {**entry.data, **entry.options}
    language = conf.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    diaspora = conf.get(CONF_DIASPORA, DEFAULT_DIASPORA)
    candle_lighting_offset = conf.get(CONF_CANDLE_LIGHT_MINUTES, DEFAULT_CANDLE_LIGHT)
    havdalah_offset = conf.get(
        CONF_HAVDALAH_OFFSET_MINUTES, DEFAULT_HAVDALAH_OFFSET_MINUTES
    )
    location = await hass.async_add_executor_job(
        partial(
            Location,
            name=hass.config.location_name,
            diaspora=diaspora,
            latitude=conf.get(CONF_LATITUDE, hass.config.latitude),
            longitude=conf.get(CONF_LONGITUDE, hass.config.longitude),
            altitude=conf.get(CONF_ELEVATION, hass.config.elevation),
            timezone=conf.get(CONF_TIME_ZONE, hass.config.time_zone),
        )
    )

    entry.runtime_data = HmemorialData(
        language,
        diaspora,
        location,
        candle_lighting_offset,
        havdalah_offset,
    )

    coordinator = HmemorialDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Chargement des plates-formes via la nouvelle API
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger l'entrée de configuration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""

    _LOGGER.debug("Migrating from version %s", entry.version)

    memorial_birthday_keys = {
        "memorial_today",
        "memorial_tomorrow",
        "memorial_current_week",
        "birthday_today",
        "birthday_tomorrow",
        "birthday_current_week",
    }
    memorial_birthday_unique_ids = {
        f"{DOMAIN}_{key}" for key in memorial_birthday_keys
    }

    @callback
    def update_unique_id(
        entity_entry: er.RegistryEntry,
    ) -> dict[str, str] | None:
        """Update unique ID of entity entry."""
        unique_id = entity_entry.unique_id
        if unique_id in memorial_birthday_unique_ids:
            key = unique_id.split(f"{DOMAIN}_", 1)[1]
            new_unique_id = f"{DOMAIN}_{entry.entry_id}_{key}"
            return {"new_unique_id": new_unique_id}

        key_translations = {
            "first_light": "alot_hashachar",
        }
        for old_key, new_key in key_translations.items():
            if unique_id.endswith(old_key):
                parts = unique_id.split("-", 1)
                if len(parts) > 1:
                    new_unique_id = f"{entry.entry_id}-{new_key}"
                    return {"new_unique_id": new_unique_id}
        return None

    if entry.version < 3:
        await er.async_migrate_entries(hass, entry.entry_id, update_unique_id)
        hass.config_entries.async_update_entry(entry, version=3)

    return True
