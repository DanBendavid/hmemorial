"""Plateforme de capteurs pour hmemorial - Version améliorée."""

import datetime as dt
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from hdate import HDateInfo, HebrewDate
from hdate.tekufot import Tekufot
from hdate.translator import get_language, set_language

try:
    from babel.dates import format_date as babel_format_date
except Exception:
    babel_format_date = None
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_ENABLE_BIRTHDAY,
    CONF_ENABLE_MEMORIAL,
    CONF_PRAYER_ONLY,
    DEFAULT_ENABLE_BIRTHDAY,
    DEFAULT_ENABLE_MEMORIAL,
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_TRADITION,
    DOMAIN,
)
from .coordinator import HmemorialDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_BABEL_LOCALE_MAP = {
    "en": "en_US",
    "fr": "fr_FR",
    "he": "he_IL",
}

# Descriptions des capteurs - les clés doivent correspondre à icons.json
SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="memorial_today",
        name="Memorial Today",
        icon="mdi:candle",
    ),
    SensorEntityDescription(
        key="memorial_tomorrow",
        name="Memorial Tomorrow",
        icon="mdi:candle",
    ),
    SensorEntityDescription(
        key="memorial_current_week",
        name="Memorial Current Week",
        icon="mdi:candle",
    ),
    SensorEntityDescription(
        key="birthday_today",
        name="Birthday Today",
        icon="mdi:cake-variant",
    ),
    SensorEntityDescription(
        key="birthday_tomorrow",
        name="Birthday Tomorrow",
        icon="mdi:cake-variant",
    ),
    SensorEntityDescription(
        key="birthday_current_week",
        name="Birthday Current Week",
        icon="mdi:cake-variant",
    ),
    SensorEntityDescription(
        key="bircat_hachanim",
        name="Bircat Hachanim",
        icon="mdi:book-open-page-variant",
    ),
    SensorEntityDescription(
        key="parasha_hayom",
        name="Parasha Hayom",
        icon="mdi:book-open-variant",
    ),
    SensorEntityDescription(
        key="tahanounim",
        name="Tahanounim",
        icon="mdi:hands-pray",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator: HmemorialDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    conf = {**entry.data, **entry.options}
    diaspora = conf.get("diaspora", True)
    tradition = conf.get("tradition", DEFAULT_TRADITION)
    language = conf.get("language", DEFAULT_LANGUAGE)

    prayer_only = conf.get(CONF_PRAYER_ONLY, False)
    enable_memorial = conf.get(CONF_ENABLE_MEMORIAL, DEFAULT_ENABLE_MEMORIAL)
    enable_birthday = conf.get(CONF_ENABLE_BIRTHDAY, DEFAULT_ENABLE_BIRTHDAY)

    sensors = []
    if not prayer_only:
        if enable_memorial:
            sensors.extend(
                [
                    MemorialSensor(
                        coordinator,
                        "memorial_today",
                        "Memorial Today",
                        target_date=datetime.now().date(),
                        language=language,
                        entry_id=entry.entry_id,
                    ),
                    MemorialSensor(
                        coordinator,
                        "memorial_tomorrow",
                        "Memorial Tomorrow",
                        target_date=datetime.now().date() + timedelta(days=1),
                        language=language,
                        entry_id=entry.entry_id,
                    ),
                    MemorialSensor(
                        coordinator,
                        "memorial_current_week",
                        "Memorial Current Week",
                        within_week=True,
                        language=language,
                        entry_id=entry.entry_id,
                    ),
                ]
            )
        if enable_birthday:
            sensors.extend(
                [
                    BirthdaySensor(
                        coordinator,
                        "birthday_today",
                        "Birthday Today",
                        target_date=datetime.now().date(),
                        language=language,
                        entry_id=entry.entry_id,
                    ),
                    BirthdaySensor(
                        coordinator,
                        "birthday_tomorrow",
                        "Birthday Tomorrow",
                        target_date=datetime.now().date() + timedelta(days=1),
                        language=language,
                        entry_id=entry.entry_id,
                    ),
                    BirthdaySensor(
                        coordinator,
                        "birthday_current_week",
                        "Birthday Current Week",
                        within_week=True,
                        language=language,
                        entry_id=entry.entry_id,
                    ),
                ]
            )

    sensors.extend(
        [
            HDatePrayerSensor(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                entity_id="bircat_hachanim",
                name="Bircat Hachanim",
                diaspora=diaspora,
                tradition=tradition,
                language=language,
            ),
            ParashaHayomSensor(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                entity_id="parasha_hayom",
                name="Parasha Hayom",
                diaspora=diaspora,
                tradition=tradition,
                language=language,
            ),
            TahanounimSensor(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                entity_id="tahanounim",
                name="Tahanounim",
                diaspora=diaspora,
                tradition=tradition,
                language=language,
            ),
        ]
    )

    async_add_entities(sensors, update_before_add=True)


class BaseSensor(CoordinatorEntity):
    """Classe de base pour tous les capteurs hmemorial."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HmemorialDataUpdateCoordinator,
        entity_id: str,
        name: str,
        entry_id: Optional[str] = None,
    ):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._entity_id = entity_id
        self._name = name
        if entry_id:
            self._attr_unique_id = f"{DOMAIN}_{entry_id}_{entity_id}"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry_id)},
                name=DEFAULT_NAME,
                manufacturer="HMemorial",
                model="Hebrew Memorial",
                entry_type=DeviceEntryType.SERVICE,
            )
        else:
            self._attr_unique_id = f"{DOMAIN}_{entity_id}"

    @property
    def name(self) -> str:
        """Nom du capteur."""
        return self._name

    @property
    def available(self) -> bool:
        """Indique si le capteur est disponible."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributs de base communs."""
        return {"attribution": ATTRIBUTION}

    def _get_week_dates(self) -> List[dt.date]:
        """Retourne la liste des 7 prochains jours."""
        today = datetime.now().date()
        return [today + timedelta(days=i) for i in range(7)]

    def _convert_to_hebrew_date(self, date: dt.date) -> Optional[HebrewDate]:
        """Convertit une date grégorienne en date hébraïque avec gestion d'erreur."""
        try:
            return HebrewDate.from_gdate(date)
        except Exception as e:
            _LOGGER.error(f"Erreur conversion date hébraïque pour {date}: {e}")
            return None


class MemorialSensor(BaseSensor):
    """Capteur pour les événements de décès (memorial)."""

    def __init__(
        self,
        coordinator: HmemorialDataUpdateCoordinator,
        entity_id: str,
        name: str,
        target_date: Optional[dt.date] = None,
        language: str = DEFAULT_LANGUAGE,
        within_week: bool = False,
        entry_id: Optional[str] = None,
    ):
        """Initialiser le capteur mémorial."""
        super().__init__(coordinator, entity_id, name, entry_id=entry_id)
        self._attr_icon = "mdi:candle"
        self._target_date = target_date
        self._within_week = within_week
        self._language = language
        self._events = []

        # Pré-calculer la date hébraïque si target_date est défini
        self._target_hdate = None
        if self._target_date:
            self._target_hdate = self._convert_to_hebrew_date(self._target_date)

    @property
    def state(self) -> int:
        """État du capteur : nombre d'événements."""
        return len(self._events)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributs supplémentaires avec événements."""
        attrs = super().extra_state_attributes
        attrs["events"] = self._events
        return attrs

    def _format_event(self, item: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Construire la structure JSON d'un événement mémorial."""
        gdate = item.get("date")
        hdate = item.get("hdate")
        gdate_str = gdate.isoformat() if isinstance(gdate, dt.date) else None
        gdate_cy = None
        gdate_cy_str = None
        hdate_str = None
        hdate_he_str = None

        if isinstance(hdate, HebrewDate):
            gdate_cy = self._get_current_year_gdate(hdate)
            if isinstance(gdate_cy, dt.date):
                gdate_cy_str = gdate_cy.isoformat()

        current_lang = get_language()
        try:
            set_language(self._language)
            if hdate is not None:
                hdate_str = str(hdate)

            set_language("he")
            if hdate is not None:
                hdate_he_str = str(hdate)
        finally:
            set_language(current_lang)

        return {
            "name": item.get("name"),
            "hdate": hdate_str,
            "hdate_he": hdate_he_str,
            "gdate": gdate_str,
            "gdate_cy": gdate_cy_str,
            "gdate_cy_weekday": self._format_weekday(gdate_cy) if gdate_cy else None,
        }

    def _format_weekday(self, date: Optional[dt.date]) -> Optional[str]:
        if not isinstance(date, dt.date):
            return None
        if babel_format_date is None:
            return f"{date.strftime('%A')} {date.day}"
        locale = _BABEL_LOCALE_MAP.get(self._language, self._language)
        try:
            return babel_format_date(date, "EEEE d", locale=locale)
        except Exception:
            return f"{date.strftime('%A')} {date.day}"

    def _get_current_year_gdate(self, hdate: HebrewDate) -> Optional[dt.date]:
        """Retourner la date gregorienne du memorial pour l'annee en cours."""
        today_hdate = self._convert_to_hebrew_date(dt.date.today())
        if not today_hdate:
            return None

        try:
            return hdate.replace(year=today_hdate.year).to_gdate()
        except Exception as e:
            _LOGGER.warning("Erreur conversion gdate_cy pour %s: %s", hdate, e)
            return None

    def _handle_coordinator_update(self) -> None:
        """Mise à jour des événements mémoriaux."""
        data_memorial = self.coordinator.data.get("memorial", [])
        filtered = []

        if self._target_date and self._target_hdate:
            # Filtrage pour une date spécifique
            filtered = [
                entry
                for entry in data_memorial
                if (
                    entry["hdate"].month == self._target_hdate.month
                    and entry["hdate"].day == self._target_hdate.day
                )
            ]

        elif self._within_week:
            # Filtrage pour la semaine courante
            week_hdates = []
            for day in self._get_week_dates():
                hdate = self._convert_to_hebrew_date(day)
                if hdate:
                    week_hdates.append((hdate.month, hdate.day))

            filtered = [
                entry
                for entry in data_memorial
                if (entry["hdate"].month, entry["hdate"].day) in week_hdates
            ]
            # Ordonner par date grégorienne de l'année en cours
            def _sort_key(item: Dict[str, Any]) -> tuple[int, dt.date]:
                hdate = item.get("hdate")
                gdate_cy = (
                    self._get_current_year_gdate(hdate)
                    if isinstance(hdate, HebrewDate)
                    else None
                )
                if not isinstance(gdate_cy, dt.date):
                    return (1, dt.date.max)
                return (0, gdate_cy)

            filtered.sort(key=_sort_key)

        self._events = [self._format_event(item) for item in filtered]

        self.async_write_ha_state()


class BirthdaySensor(BaseSensor):
    """Capteur pour les événements d'anniversaire."""

    def __init__(
        self,
        coordinator: HmemorialDataUpdateCoordinator,
        entity_id: str,
        name: str,
        target_date: Optional[dt.date] = None,
        within_week: bool = False,
        language: str = DEFAULT_LANGUAGE,
        entry_id: Optional[str] = None,
    ):
        """Initialiser le capteur anniversaire."""
        super().__init__(coordinator, entity_id, name, entry_id=entry_id)
        self._attr_icon = "mdi:cake-variant"
        self._target_date = target_date
        self._within_week = within_week
        self._language = language
        self._events = []

    @property
    def state(self) -> int:
        """État du capteur : nombre d'événements."""
        return len(self._events)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributs supplémentaires avec événements."""
        attrs = super().extra_state_attributes
        attrs["events"] = self._events
        return attrs

    def _format_weekday(self, date: Optional[dt.date]) -> Optional[str]:
        if not isinstance(date, dt.date):
            return None
        if babel_format_date is None:
            return f"{date.strftime('%A')} {date.day}"
        locale = _BABEL_LOCALE_MAP.get(self._language, self._language)
        try:
            return babel_format_date(date, "EEEE d", locale=locale)
        except Exception:
            return f"{date.strftime('%A')} {date.day}"

    def _get_current_year_gdate(self, date: dt.date) -> Optional[dt.date]:
        """Return the birthday date for the current year."""
        if not isinstance(date, dt.date):
            return None
        today = dt.date.today()
        try:
            return date.replace(year=today.year)
        except ValueError:
            if date.month == 2 and date.day == 29:
                return dt.date(today.year, 2, 28)
            return None

    def _calculate_age(
        self, birth_date: dt.date, event_date: Optional[dt.date]
    ) -> Optional[int]:
        if not isinstance(birth_date, dt.date) or birth_date.year <= 0:
            return None
        if not isinstance(event_date, dt.date):
            return None
        age = event_date.year - birth_date.year
        if age < 0:
            return None
        return age

    def _format_event(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Build the JSON structure for a birthday event."""
        gdate = item.get("date")
        gdate_cy = self._get_current_year_gdate(gdate) if gdate else None
        gdate_cy_str = gdate_cy.isoformat() if isinstance(gdate_cy, dt.date) else None
        age = self._calculate_age(gdate, gdate_cy) if gdate else None
        return {
            "name": item.get("name"),
            "gdate_cy": gdate_cy_str,
            "age": age,
            "gdate_cy_weekday": self._format_weekday(gdate_cy) if gdate_cy else None,
        }

    def _handle_coordinator_update(self) -> None:
        """Mise à jour des événements d'anniversaire."""
        data_birthday = self.coordinator.data.get("birthday", [])
        filtered = []

        if self._target_date:
            # Filtrage pour une date spécifique (mois + jour seulement)
            filtered = [
                entry
                for entry in data_birthday
                if (
                    entry["date"].month == self._target_date.month
                    and entry["date"].day == self._target_date.day
                )
            ]

        elif self._within_week:
            # Filtrage pour la semaine courante
            week_dates = [(day.month, day.day) for day in self._get_week_dates()]

            filtered = [
                entry
                for entry in data_birthday
                if (entry["date"].month, entry["date"].day) in week_dates
            ]

        self._events = [self._format_event(item) for item in filtered]

        self.async_write_ha_state()


class HDatePrayerSensor(BaseSensor):
    """Capteur pour la prière du jour et les tekoufot."""

    def __init__(
        self,
        coordinator: HmemorialDataUpdateCoordinator,
        entity_id: str,
        name: str = "Bircat Hachanim",
        entry_id: Optional[str] = None,
        diaspora: bool = True,
        tradition: str = "ashkenazi",
        language: str = "he",
    ):
        """Initialiser le capteur de prière."""
        suffix = f"{language}_{'diaspora' if diaspora else 'israel'}_{tradition}"
        full_name = f"{name} ({suffix})"
        super().__init__(coordinator, f"{entity_id}_{suffix}", full_name, entry_id=entry_id)
        self._attr_icon = "mdi:book-open-page-variant"

        self._diaspora = diaspora
        self._tradition = tradition
        self._language = language
        self._state = None
        self._prayer_attributes = {}

    @property
    def state(self) -> Optional[str]:
        """État du capteur : prière du jour."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributs avec informations de prière et tekoufot."""
        attrs = super().extra_state_attributes
        attrs.update(self._prayer_attributes)
        return attrs

    def _handle_coordinator_update(self) -> None:
        """Mise à jour des informations de prière."""
        try:
            today = dt.date.today()
            set_language(self._language)

            tek = Tekufot(
                date=today, diaspora=self._diaspora, tradition=self._tradition
            )

            self._state = tek.get_prayer_for_date()
            self._prayer_attributes = {}

            # Ajouter les 4 tekoufot comme attributs
            for name in ["Nissan", "Tammuz", "Tishrei", "Tevet"]:
                key = f"tekufa_{name.lower()}"
                try:
                    value = tek.get_tekufa(name)
                    if isinstance(value, dt.datetime):
                        value = value.strftime("%Y-%m-%d %H:%M")
                    self._prayer_attributes[key] = value
                except Exception as e:
                    _LOGGER.warning(f"Erreur récupération tekufa {name}: {e}")
                    self._prayer_attributes[key] = None

        except Exception as e:
            _LOGGER.error(f"Erreur mise à jour capteur prière: {e}")
            self._state = "Erreur"
            self._prayer_attributes = {"error": str(e)}

        self.async_write_ha_state()


class ParashaHayomSensor(BaseSensor):
    """Capteur pour la parasha du jour."""

    def __init__(
        self,
        coordinator: HmemorialDataUpdateCoordinator,
        entity_id: str,
        name: str = "Parasha Hayom",
        entry_id: Optional[str] = None,
        diaspora: bool = True,
        tradition: str = "ashkenazi",
        language: str = "he",
    ):
        """Initialiser le capteur de parasha."""
        suffix = f"{language}_{'diaspora' if diaspora else 'israel'}_{tradition}"
        full_name = f"{name} ({suffix})"
        super().__init__(coordinator, f"{entity_id}_{suffix}", full_name, entry_id=entry_id)
        self._attr_icon = "mdi:book-open-variant"
        self._diaspora = diaspora
        self._tradition = tradition
        self._language = language
        self._state = None
        self._parasha_attributes = {}

    @property
    def state(self) -> Optional[str]:
        """Etat du capteur : parasha du jour."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributs avec details de parasha."""
        attrs = super().extra_state_attributes
        attrs.update(self._parasha_attributes)
        return attrs

    def _build_hdate_info(self, date: dt.date) -> HDateInfo:
        """Construire HDateInfo avec compatibilite de signature."""
        try:
            return HDateInfo(date, self._diaspora)
        except TypeError:
            return HDateInfo(date=date, diaspora=self._diaspora)

    def _handle_coordinator_update(self) -> None:
        """Mise a jour de la parasha du jour."""
        try:
            today = dt.date.today()
            set_language(self._language)

            hdate_info = self._build_hdate_info(today)
            parasha = getattr(hdate_info, "parasha", None)
            if callable(parasha):
                parasha = parasha()

            if isinstance(parasha, (list, tuple)):
                parasha = ", ".join(str(item) for item in parasha if item)

            self._state = parasha or None
            self._parasha_attributes = {}
        except Exception as e:
            _LOGGER.error(f"Erreur mise a jour parasha: {e}")
            self._state = "Erreur"
            self._parasha_attributes = {"error": str(e)}

        self.async_write_ha_state()


class TahanounimSensor(BaseSensor):
    """Capteur pour Tahanounim selon le minhag."""

    def __init__(
        self,
        coordinator: HmemorialDataUpdateCoordinator,
        entity_id: str,
        name: str = "Tahanounim",
        entry_id: Optional[str] = None,
        diaspora: bool = True,
        tradition: str = "ashkenazi",
        language: str = "he",
    ):
        """Initialiser le capteur Tahanounim."""
        suffix = f"{language}_{'diaspora' if diaspora else 'israel'}_{tradition}"
        full_name = f"{name} ({suffix})"
        super().__init__(coordinator, f"{entity_id}_{suffix}", full_name, entry_id=entry_id)
        self._attr_icon = "mdi:hands-pray"
        self._diaspora = diaspora
        self._tradition = tradition
        self._language = language
        self._state = None
        self._tahanounim_attributes = {}

    @property
    def state(self) -> Optional[str]:
        """Etat du capteur : yes/no/without_nefilat_apayim."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributs avec details de la decision."""
        attrs = super().extra_state_attributes
        attrs.update(self._tahanounim_attributes)
        return attrs

    def _localize_state(self, state_key: str) -> str:
        labels = {
            "en": {
                "yes": "Taḥanoun is recited with Nefilat Apayim",
                "no": "Taḥanoun is not recited",
                "without_nefilat_apayim": "Taḥanoun is recited (without Nefilat Apayim)",
            },
            "fr": {
                "yes": "Avec Taḥanounim et Nefilat Apayim",
                "no": "Sans Taḥanounim",
                "without_nefilat_apayim": "Sans nefilat apayim",
            },
            "he": {
                "yes": "עִם תַּחֲנוּנִים וּנְפִילַת אַפַּיִם",
                "no": "לְלֹא תַּחֲנוּנִים",
                "without_nefilat_apayim": "עִם תַּחֲנוּנִים – בְּלֹא נְפִילַת אַפַּיִם",
            },
        }
        lang = self._language if self._language in labels else "en"
        return labels[lang].get(state_key, state_key)

    def _build_hdate_info(self, date: dt.date) -> HDateInfo:
        """Construire HDateInfo avec compatibilite de signature."""
        try:
            return HDateInfo(date, self._diaspora)
        except TypeError:
            return HDateInfo(date=date, diaspora=self._diaspora)

    def _get_bool_attr(self, obj: Any, names: list[str]) -> bool:
        for name in names:
            value = getattr(obj, name, None)
            if callable(value):
                try:
                    value = value()
                except Exception:
                    continue
            if isinstance(value, bool):
                return value
        return False

    def _get_holidays(self, obj: Any) -> list[str]:
        value = getattr(obj, "holidays", None)
        if value is None:
            value = getattr(obj, "holiday", None)
        if callable(value):
            try:
                value = value()
            except Exception:
                value = None
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value if item]

    def _holiday_contains(self, holidays: list[str], keywords: list[str]) -> bool:
        for holiday in holidays:
            for key in keywords:
                if key.lower() in holiday.lower():
                    return True
        return False

    def _is_yom_tov(self, info: HDateInfo) -> bool:
        if self._get_bool_attr(info, ["is_yom_tov", "is_yomtov", "yom_tov"]):
            return True
        holidays = self._get_holidays(info)
        return self._holiday_contains(holidays, ["yom tov", "yomtov"])

    def _is_hol_hamoed(self, info: HDateInfo) -> bool:
        if self._get_bool_attr(info, ["is_hol_hamoed", "is_chol_hamoed", "hol_hamoed"]):
            return True
        holidays = self._get_holidays(info)
        return self._holiday_contains(holidays, ["hol hamoed", "chol hamoed"])

    def _is_rosh_chodesh(self, info: HDateInfo) -> bool:
        if self._get_bool_attr(
            info, ["is_rosh_chodesh", "is_rosh_hodesh", "rosh_chodesh"]
        ):
            return True
        holidays = self._get_holidays(info)
        return self._holiday_contains(holidays, ["rosh chodesh", "rosh hodesh"])

    def _is_chanukah(self, info: HDateInfo) -> bool:
        if self._get_bool_attr(info, ["is_chanukah", "is_hanukkah"]):
            return True
        holidays = self._get_holidays(info)
        return self._holiday_contains(holidays, ["chanukah", "hanukkah"])

    def _is_purim(self, info: HDateInfo) -> bool:
        if self._get_bool_attr(info, ["is_purim"]):
            return True
        holidays = self._get_holidays(info)
        return self._holiday_contains(holidays, ["purim"])

    def _is_lag_baomer(self, info: HDateInfo) -> bool:
        omer = getattr(info, "omer_day", None)
        if omer is None:
            omer = getattr(info, "omer", None)
        try:
            if isinstance(omer, int) and omer == 33:
                return True
        except Exception:
            pass
        holidays = self._get_holidays(info)
        return self._holiday_contains(
            holidays, ["lag baomer", "lag ba'omer", "lag baomer"]
        )

    def _is_isru_chag(self, info: HDateInfo, yesterday_info: HDateInfo) -> bool:
        if self._get_bool_attr(info, ["is_isru_chag", "isru_chag"]):
            return True
        holidays = self._get_holidays(info)
        if self._holiday_contains(holidays, ["isru", "isru chag", "isru hag"]):
            return True
        if (not self._is_yom_tov(info)) and self._is_yom_tov(yesterday_info):
            return True
        return False

    def _is_nissan(self, date: dt.date) -> bool:
        try:
            hdate = HebrewDate.from_gdate(date)
            return getattr(hdate, "month", None) == 1
        except Exception:
            return False

    def _handle_coordinator_update(self) -> None:
        """Mise a jour du statut Tahanounim."""
        try:
            today = dt.date.today()
            set_language(self._language)

            info = self._build_hdate_info(today)
            tomorrow_info = self._build_hdate_info(today + dt.timedelta(days=1))
            yesterday_info = self._build_hdate_info(today - dt.timedelta(days=1))

            reasons_no: list[str] = []
            reasons_partial: list[str] = []

            is_shabbat = today.weekday() == 5 or self._get_bool_attr(
                info, ["is_shabbat", "shabbat"]
            )
            if is_shabbat:
                reasons_no.append("shabbat")

            if self._is_yom_tov(info):
                reasons_no.append("yom_tov")

            if self._is_hol_hamoed(info):
                reasons_no.append("hol_hamoed")

            if self._is_rosh_chodesh(info):
                reasons_no.append("rosh_chodesh")

            if self._is_chanukah(info):
                reasons_no.append("chanukah")

            if self._is_purim(info):
                reasons_no.append("purim")

            if self._is_lag_baomer(info):
                reasons_no.append("lag_baomer")

            if self._is_isru_chag(info, yesterday_info):
                reasons_partial.append("isru_chag")

            if (not self._is_yom_tov(info)) and self._is_yom_tov(tomorrow_info):
                reasons_partial.append("erev_yom_tov")

            if self._is_nissan(today):
                reasons_partial.append("nissan")

            # Tradition-specific adjustments
            if self._tradition == "sephardi":
                # Sephardi: strict, no partials
                reasons_no.extend(reasons_partial)
                reasons_partial = []
            else:
                # Ashkenazi: no Tahanounim for these, partial for others
                pass

            if reasons_no:
                state_key = "no"
            elif reasons_partial and self._tradition != "sephardi":
                state_key = "without_nefilat_apayim"
            else:
                state_key = "yes"

            self._state = self._localize_state(state_key)
            self._tahanounim_attributes = {
                "tradition": self._tradition,
                "diaspora": self._diaspora,
                "state_key": state_key,
                "reasons_no": reasons_no,
                "reasons_partial": reasons_partial,
            }
        except Exception as e:
            _LOGGER.error(f"Erreur mise a jour Tahanounim: {e}")
            self._state = "Erreur"
            self._tahanounim_attributes = {"error": str(e)}

        self.async_write_ha_state()
