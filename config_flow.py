# custom_components/hmemorial/config_flow.py

"""Flux de configuration pour hmemorial."""
import logging
import zoneinfo
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_ELEVATION, CONF_TIME_ZONE
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    OPTIONS_SCHEMA,  # Un exemple de schéma d'options défini dans const.py
)

_LOGGER = logging.getLogger(__name__)


def _get_data_schema(hass: HomeAssistant) -> vol.Schema:
    """Créer le schéma Voluptuous pour la configuration initiale."""
    # Valeurs par défaut récupérées de la config HA
    default_lat = hass.config.latitude
    default_lon = hass.config.longitude
    default_elev = hass.config.elevation
    default_tz = hass.config.time_zone

    # On peut regrouper 'latitude' et 'longitude' dans un dict "location",
    # ou bien les exposer séparément.
    # Ici, on les expose séparément pour la lisibilité.
    return vol.Schema(
        {
            vol.Optional(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
            vol.Optional(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
            vol.Optional(CONF_ELEVATION, default=default_elev): vol.Coerce(int),
            vol.Optional(CONF_TIME_ZONE, default=default_tz): vol.In(sorted(zoneinfo.available_timezones())),
        }
    )


class HmemorialConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer le flux de configuration pour Hmemorial."""

    VERSION = 1  # Numéro de version du schéma

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
            # On pourrait effectuer ici des vérifications supplémentaires
            # (Ex: tester une API, vérifier un fichier, etc.)
            # Si tout va bien, on crée l’entrée
            return self.async_create_entry(
                title=DEFAULT_NAME,  # Nom de l'entrée dans HA
                data=user_input,     # Données finales stockées dans la ConfigEntry
            )

        # Si on n’a pas de saisie, on affiche le formulaire
        return self.async_show_form(
            step_id="user",
            data_schema=_get_data_schema(self.hass),
            errors=errors,
        )

    # Si vous prévoyez d’autres étapes (reconfigure, etc.), vous pouvez
    # les ajouter ici, sous forme de méthodes async_step_xxx.


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
            return self.async_create_entry(data=user_input)

        # On utilise un schéma défini dans const.py (OPTIONS_SCHEMA) ou on peut le construire ici
        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS_SCHEMA,
        )
