# custom_components/hmemorial/__init__.py

"""Initialisation du composant hmemorial."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import HmemorialDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Configuration initiale du composant hmemorial."""
    # Initialisez les données dans hass.data
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configurer hmemorial à partir d'une entrée de configuration."""
    # Initialiser le coordonnateur
    coordinator = HmemorialDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Stocker le coordonnateur dans hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator
    }

    # Configurer les plateformes (capteurs)
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Décharger une entrée de configuration."""
    # Décharger les plateformes
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        # Supprimer le coordonnateur des données stockées
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

