# coordinator.py
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .utils import read_data_birthday, read_data_memorial

_LOGGER = logging.getLogger(__name__)


class HmemorialDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self):
        # Lire les deux fichiers (de façon asynchrone)
        data_memorial = await read_data_memorial(self.hass)
        data_birthday = await read_data_birthday(self.hass)

        # On peut stocker les deux listes dans self.data
        return {
            "memorial": data_memorial,
            "birthday": data_birthday,
        }
