"""Plateforme de capteurs pour hmemorial."""
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTRIBUTION
from .coordinator import HmemorialDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
):
    """Configurer les capteurs à partir de l'entrée de configuration."""
    coordinator: HmemorialDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = [
        # Mémorial
        MemorialSensor(coordinator, "Memorial Today", target_date=datetime.now().date()),
        MemorialSensor(coordinator, "Memorial Tomorrow", target_date=(datetime.now().date() + timedelta(days=1))),
        MemorialSensor(coordinator, "Memorial Current Week", within_week=True),

        # Anniversaires
        BirthdaySensor(coordinator, "Birthday Today", target_date=datetime.now().date()),
        BirthdaySensor(coordinator, "Birthday Tomorrow", target_date=(datetime.now().date() + timedelta(days=1))),
        BirthdaySensor(coordinator, "Birthday Current Week", within_week=True),
    ]

    async_add_entities(sensors, update_before_add=True)


class MemorialSensor(CoordinatorEntity):
    """Capteur pour les événements de décès (memorial)."""

    _attr_should_poll = False

    def __init__(self, coordinator: HmemorialDataUpdateCoordinator, name: str,
                 target_date=None, within_week=False):
        """Initialiser le capteur."""
        super().__init__(coordinator)
        self._name = name
        self._target_date = target_date
        self._within_week = within_week
        self._events = []

    @property
    def name(self):
        """Nom du capteur."""
        return self._name

    @property
    def state(self):
        """État du capteur : nombre d'événements correspondant au filtrage."""
        return len(self._events)

    @property
    def extra_state_attributes(self):
        """Attributs supplémentaires : liste des événements + attribution."""
        return {
            "events": self._events,
            "attribution": ATTRIBUTION,
        }

    @property
    def available(self):
        """Indique si le capteur est disponible (mise à jour réussie)."""
        return self.coordinator.last_update_success

    def _handle_coordinator_update(self):
        """Méthode appelée quand le coordinator est mis à jour."""
        data_memorial = self.coordinator.data.get("memorial", [])
        # Filtrez selon target_date / within_week
        filtered = []

        if self._target_date:
            # On compare la date grégorienne stockée à self._target_date
            for entry in data_memorial:
                if entry["date"] == self._target_date:
                    filtered.append(entry)

        elif self._within_week:
            # On définit la "semaine courante" comme du jour J à J+6
            # ou toute autre logique de calcul
            today = datetime.now().date()
            end_of_week = today + timedelta(days=6)
            for entry in data_memorial:
                if today <= entry["date"] <= end_of_week:
                    filtered.append(entry)

        self._events = [
            f"{item['name']} ({item['date']})"
            for item in filtered
        ]

        self.async_write_ha_state()


class BirthdaySensor(CoordinatorEntity):
    """Capteur pour les événements d'anniversaire (birthday)."""

    _attr_should_poll = False

    def __init__(self, coordinator: HmemorialDataUpdateCoordinator, name: str,
                 target_date=None, within_week=False):
        """Initialiser le capteur."""
        super().__init__(coordinator)
        self._name = name
        self._target_date = target_date
        self._within_week = within_week
        self._events = []

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return len(self._events)

    @property
    def extra_state_attributes(self):
        return {
            "events": self._events,
            "attribution": ATTRIBUTION,
        }

    @property
    def available(self):
        return self.coordinator.last_update_success

    def _handle_coordinator_update(self):
        """Appelé quand le coordinator a de nouvelles données."""
        data_birthday = self.coordinator.data.get("birthday", [])
        filtered = []

        if self._target_date:
            for entry in data_birthday:
                # On compare uniquement mois+jour, si on veut ignorer l'année
                # ou on compare la date entière si on veut l'année exacte
                if entry["date"].month == self._target_date.month and \
                   entry["date"].day == self._target_date.day:
                    filtered.append(entry)

        elif self._within_week:

            today = datetime.now().date()
            end_of_week = today + timedelta(days=6)
            for entry in data_birthday:
                if today <= entry["date"] <= end_of_week:
                    filtered.append(entry)

        self._events = [
            f"{item['name']} ({item['date']})"
            for item in filtered
        ]

        self.async_write_ha_state()
