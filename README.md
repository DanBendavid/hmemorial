# HMemorial (Hebrew Memorial)

Home Assistant custom integration to track Hebrew memorial days (yahrzeit),
birthdays, and daily prayer indicators (Bircat Hachanim, Parasha Hayom,
Tahanounim). Uses the `hdate` library for Jewish calendar calculations.

## Features
- Memorial/yahrzeit sensors for today, tomorrow, and current week
- Birthday sensors for today, tomorrow, and current week
- Prayer sensors: Bircat Hachanim (with tekufot attributes), Parasha Hayom,
  and Tahanounim
- Language selection (he/fr/en), diaspora vs Israel, and tradition
  (ashkenazi/sephardi)
- Optional per-feature toggles (enable/disable Memorial and Birthday sensors)
- Optional "prayer only" mode
- Location picker with map (country/city search + pin)
- Optional Lovelace cards for memorials and birthdays

## Installation

### HACS (custom repository)
1. HACS -> Integrations -> menu -> Custom repositories.
2. Add `https://github.com/DanBendavid/hmemorial` as type `Integration`.
3. Install and restart Home Assistant.

### Manual
1. Copy `custom_components/hmemorial` into your HA config directory.
2. Restart Home Assistant.

## Configuration
This integration uses a config flow.
1. Settings -> Devices & Services -> Add Integration -> `Hebrew Memorial`.
2. Choose options:
   - Tradition: `ashkenazi` or `sephardi`
   - Language: `he`, `fr`, `en`
   - Diaspora: outside Israel
   - Enable memorials (create memorial sensors)
   - Enable birthdays (create birthday sensors)
   - Prayer sensors only: create only Bircat Hachanim, Parasha Hayom,
     and Tahanounim
   - Location (map picker), elevation, and time zone
   - Candle lighting minutes before sunset (default 18)
   - Havdalah minutes after sunset (0 uses default 8.5 degrees)

Notes:
- If "Prayer sensors only" is enabled, Memorial and Birthday sensors are not created.
- Location, elevation, and time zone default to your Home Assistant settings.

## Data files
The integration reads two files in `custom_components/hmemorial/`:
- `data_memorial.txt` (Hebrew dates)
- `data_birthday.txt` (Gregorian dates)

Memorial file format (name, day, month, year in Hebrew calendar; year can be
empty):

```text
Name, day, month, year
Sarah bat Tamo, 6, 5, 5756
```

Birthday file format (name, YYYY-MM-DD):

```text
Name, YYYY-MM-DD
Dan, 1975-05-15
```

Notes:
- Files are read every 60 seconds.
- If the memorial year is empty, the default is 5785.
- HACS updates may overwrite files inside `custom_components/hmemorial`;
  keep a backup if you edit them.

## Entities
Memorial sensors (state = number of events, attributes include `events` list):
- Memorial Today
- Memorial Tomorrow
- Memorial Current Week

Birthday sensors (state = number of events, attributes include `events` list):
- Birthday Today
- Birthday Tomorrow
- Birthday Current Week

Prayer sensors (state = string):
- Bircat Hachanim (`tekufa_nissan`, `tekufa_tammuz`, `tekufa_tishrei`,
  `tekufa_tevet`)
- Parasha Hayom
- Tahanounim (`state_key`, `reasons_no`, `reasons_partial`, `tradition`,
  `diaspora`)

Sensor names include a suffix like `en_diaspora_ashkenazi` based on options.

## Lovelace cards (optional)
This integration ships two simple cards: one for memorial events and one for birthdays.

1. Add resource:
   - URL: `/hackfiles/hmemorial-card/hmemorial-card.js`
   - Type: `module`
2. Example cards:

```yaml
type: custom:hmemorial-card
entity: sensor.hmemorial_memorial_current_week
title: 🕯️Memorials this week
```

```yaml
type: custom:hmemorial-birthday-card
entity: sensor.hmemorial_birthday_current_week
title: 🎂 Birthdays this week
```

Note: The cards expect `events` attributes with objects (the memorial and birthday sensors).

## Troubleshooting
- Check Home Assistant logs for `hmemorial`.
- Validate file formats and dates.
- Ensure time zone and location are correct.

## License
GPL-3.0 (see `LICENSE`).
