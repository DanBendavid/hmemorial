# coordinator.py
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, FILE_PATH_MEMORIAL, FILE_PATH_BIRTHDAY
from .utils import read_data_memorial, read_data_birthday

_LOGGER = logging.getLogger(__name__)

class HmemorialDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self):
        # Lire les deux fichiers
        data_memorial = read_data_memorial(self.hass)
        data_birthday = read_data_birthday(self.hass)

        # On peut stocker les deux listes dans self.data
        return {
            "memorial": data_memorial,
            "birthday": data_birthday,
        }