# custom_components/hmemorial/config_flow.py

"""Flux de configuration pour hmemorial."""
import logging
import zoneinfo
from functools import partial
from typing import Any, get_args

import voluptuous as vol
from hdate.translator import Language
from homeassistant import config_entries
from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_TIME_ZONE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    LanguageSelector,
    LanguageSelectorConfig,
    LocationSelector,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    CONF_CANDLE_LIGHT_MINUTES,
    CONF_DIASPORA,
    CONF_ENABLE_BIRTHDAY,
    CONF_ENABLE_MEMORIAL,
    CONF_HAVDALAH_OFFSET_MINUTES,
    CONF_PRAYER_ONLY,
    CONF_TRADITION,
    DEFAULT_CANDLE_LIGHT,
    DEFAULT_DIASPORA,
    DEFAULT_ENABLE_BIRTHDAY,
    DEFAULT_ENABLE_MEMORIAL,
    DEFAULT_HAVDALAH_OFFSET_MINUTES,
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_TRADITION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

NUSACHIM = ["ashkenazi", "sephardi"]
# LANGUAGES = ["he", "fr", "en"]


def _tradition_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                {"value": value, "label": value.capitalize()} for value in NUSACHIM
            ]
        )
    )


def _apply_location_to_input(user_input: dict[str, Any]) -> dict[str, Any]:
    location = user_input.pop(CONF_LOCATION, None)
    if isinstance(location, dict):
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None:
            user_input[CONF_LATITUDE] = float(lat)
        if lon is not None:
            user_input[CONF_LONGITUDE] = float(lon)
    return user_input


def _get_options_schema(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> vol.Schema:
    """Créer le schéma des options."""
    merged = {**entry.data, **entry.options}
    default_lat = merged.get(CONF_LATITUDE, hass.config.latitude)
    default_lon = merged.get(CONF_LONGITUDE, hass.config.longitude)
    default_elev = merged.get(CONF_ELEVATION, hass.config.elevation)
    default_tz = merged.get(CONF_TIME_ZONE, hass.config.time_zone)
    location_default = {"latitude": default_lat, "longitude": default_lon}
    return vol.Schema(
        {
            vol.Optional(
                CONF_TRADITION, default=merged.get(CONF_TRADITION, DEFAULT_TRADITION)
            ): _tradition_selector(),
            vol.Optional(
                CONF_LANGUAGE, default=merged.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
            ): LanguageSelector(
                LanguageSelectorConfig(languages=list(get_args(Language)))
            ),
            vol.Optional(
                CONF_DIASPORA, default=merged.get(CONF_DIASPORA, DEFAULT_DIASPORA)
            ): BooleanSelector(),
            vol.Optional(
                CONF_ENABLE_MEMORIAL,
                default=merged.get(CONF_ENABLE_MEMORIAL, DEFAULT_ENABLE_MEMORIAL),
            ): BooleanSelector(),
            vol.Optional(
                CONF_ENABLE_BIRTHDAY,
                default=merged.get(CONF_ENABLE_BIRTHDAY, DEFAULT_ENABLE_BIRTHDAY),
            ): BooleanSelector(),
            vol.Optional(
                CONF_PRAYER_ONLY, default=merged.get(CONF_PRAYER_ONLY, False)
            ): BooleanSelector(),
            vol.Optional(CONF_LOCATION, default=location_default): LocationSelector(),
            vol.Optional(CONF_ELEVATION, default=default_elev): vol.Coerce(int),
            vol.Optional(CONF_TIME_ZONE, default=default_tz): vol.In(
                sorted(zoneinfo.available_timezones())
            ),
            vol.Optional(
                CONF_CANDLE_LIGHT_MINUTES,
                default=merged.get(CONF_CANDLE_LIGHT_MINUTES, DEFAULT_CANDLE_LIGHT),
            ): int,
            vol.Optional(
                CONF_HAVDALAH_OFFSET_MINUTES,
                default=merged.get(
                    CONF_HAVDALAH_OFFSET_MINUTES, DEFAULT_HAVDALAH_OFFSET_MINUTES
                ),
            ): int,
        }
    )


def _get_data_schema(
    hass: HomeAssistant, prayer_only_default: bool = False
) -> vol.Schema:
    """Créer le schéma Voluptuous pour la configuration initiale."""
    # Valeurs par défaut récupérées de la config HA
    default_lat = hass.config.latitude
    default_lon = hass.config.longitude
    default_elev = hass.config.elevation
    default_tz = hass.config.time_zone
    location_default = {"latitude": default_lat, "longitude": default_lon}

    # On peut regrouper 'latitude' et 'longitude' dans un dict "location",
    # ou bien les exposer séparément.
    # Ici, on les expose séparément pour la lisibilité.
    return vol.Schema(
        {
            vol.Required(CONF_TRADITION, default=DEFAULT_TRADITION): _tradition_selector(),
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): LanguageSelector(
                LanguageSelectorConfig(languages=list(get_args(Language)))
            ),
            vol.Required(CONF_DIASPORA, default=DEFAULT_DIASPORA): BooleanSelector(),
            vol.Optional(
                CONF_ENABLE_MEMORIAL, default=DEFAULT_ENABLE_MEMORIAL
            ): BooleanSelector(),
            vol.Optional(
                CONF_ENABLE_BIRTHDAY, default=DEFAULT_ENABLE_BIRTHDAY
            ): BooleanSelector(),
            vol.Optional(
                CONF_PRAYER_ONLY, default=prayer_only_default
            ): BooleanSelector(),
            vol.Optional(CONF_LOCATION, default=location_default): LocationSelector(),
            vol.Optional(CONF_ELEVATION, default=default_elev): vol.Coerce(int),
            vol.Optional(CONF_TIME_ZONE, default=default_tz): vol.In(
                sorted(zoneinfo.available_timezones())
            ),
        }
    )


class HmemorialConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer le flux de configuration pour Hmemorial."""

    VERSION = 3  # Numéro de version du schéma

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "HmemorialOptionsFlowHandler":
        """Renvoyer la classe de gestion des options."""
        return HmemorialOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """
        Étape principale de configuration, appelée quand l'utilisateur
        ajoute l'intégration via l'UI.
        """
        errors = {}

        if user_input is not None:
            user_input = _apply_location_to_input(user_input)
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data=user_input,
            )

        prayer_only_default = bool(self._async_current_entries())
        return self.async_show_form(
            step_id="user",
            data_schema=_get_data_schema(self.hass, prayer_only_default),
            errors=errors,
        )


class HmemorialOptionsFlowHandler(config_entries.OptionsFlow):
    """Gérer les options pour une instance existante de Hmemorial."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise le flux d’options."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """
        Étape initiale (unique) du flux d'options.
        L'utilisateur peut modifier les options définies dans const.py.
        """
        if user_input is not None:
            # On enregistre les options
            user_input = _apply_location_to_input(user_input)
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(self.hass, self.config_entry),
        )
