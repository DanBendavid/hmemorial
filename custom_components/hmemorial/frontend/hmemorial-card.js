const HM_LANG_MAP = {
  en: "en-US",
  fr: "fr-FR",
  he: "he-IL",
};

const HM_I18N = {
  en: {
    title: "Hmemorial",
    notFound: "Entity not found: {entity}",
    emptyEvents: "No events",
    birthdayTitle: "Birthdays",
    emptyBirthdays: "No birthdays this week.",
    birthdayTodaySuffix: "celebrates a birthday today.",
    birthdayOnSuffix: "celebrates a birthday on {weekday}.",
    birthdayDefaultSuffix: "celebrates a birthday.",
    yearsSuffix: " years",
  },
  fr: {
    title: "Hmemorial",
    notFound: "Entite introuvable: {entity}",
    emptyEvents: "Aucun evenement",
    birthdayTitle: "Anniversaires",
    emptyBirthdays: "Aucun anniversaire cette semaine.",
    birthdayTodaySuffix: "fete son anniversaire aujourd'hui.",
    birthdayOnSuffix: "fete son anniversaire ce {weekday}.",
    birthdayDefaultSuffix: "fete son anniversaire.",
    yearsSuffix: " ans",
  },
  he: {
    title: "Hmemorial",
    notFound: "היישות לא נמצאה: {entity}",
    emptyEvents: "אין אירועים",
    birthdayTitle: "ימי הולדת",
    emptyBirthdays: "אין ימי הולדת השבוע.",
    birthdayTodaySuffix: "חוגג יום הולדת היום.",
    birthdayOnSuffix: "חוגג יום הולדת ביום {weekday}.",
    birthdayDefaultSuffix: "חוגג יום הולדת.",
    yearsSuffix: " שנים",
  },
};

const hmNormalizeLang = (lang) => {
  if (!lang) {
    return "en";
  }
  const lower = String(lang).toLowerCase();
  if (lower.startsWith("fr")) {
    return "fr";
  }
  if (lower.startsWith("he")) {
    return "he";
  }
  return "en";
};

const hmGetLang = (config, hass) =>
  hmNormalizeLang(
    config.language ||
      config.lang ||
      (hass && hass.language) ||
      (hass && hass.locale && hass.locale.language),
  );

const hmT = (lang, key, vars) => {
  const dict = HM_I18N[lang] || HM_I18N.en;
  const template = dict[key] || "";
  return template.replace(/\{(\w+)\}/g, (match, name) =>
    Object.prototype.hasOwnProperty.call(vars || {}, name) ? vars[name] : match,
  );
};

const hmWeekdayLabel = (date, lang) => {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    return null;
  }
  const locale = HM_LANG_MAP[lang] || HM_LANG_MAP.en;
  try {
    const weekday = date.toLocaleDateString(locale, { weekday: "long" });
    return `${weekday} ${date.getDate()}`;
  } catch (err) {
    const weekday = date.toLocaleDateString("en-US", { weekday: "long" });
    return `${weekday} ${date.getDate()}`;
  }
};

class HmemorialCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("entity is required");
    }

    this._config = {
      title: null,
      show_age: true,
      ...config,
    };

    if (!this._card) {
      this._card = document.createElement("ha-card");
      this._content = document.createElement("div");
      this._content.className = "card-content";
      this._card.appendChild(this._content);

      const style = document.createElement("style");
      style.textContent = `
        .card-content {
          padding: 8px 16px 12px 16px;
        }
        .event {
          border-left: 3px solid var(--primary-color);
          margin: 8px 0;
          padding: 4px 0 4px 10px;
        }
        .name {
          font-weight: 600;
        }
        .meta {
          color: var(--secondary-text-color);
          font-size: 0.9em;
          margin-top: 2px;
        }
        .empty {
          color: var(--secondary-text-color);
          padding: 8px 0;
        }
      `;
      this._card.appendChild(style);
      this.appendChild(this._card);
    }
  }

  set hass(hass) {
    if (!this._config) {
      return;
    }

    const stateObj = hass.states[this._config.entity];
    const lang = hmGetLang(this._config, hass);
    const strings = HM_I18N[lang] || HM_I18N.en;
    const title =
      this._config.title ||
      (stateObj && stateObj.attributes && stateObj.attributes.friendly_name) ||
      strings.title;

    this._card.header = title;
    this._card.setAttribute("dir", lang === "he" ? "rtl" : "ltr");
    this._content.innerHTML = "";

    if (!stateObj) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = hmT(lang, "notFound", { entity: this._config.entity });
      this._content.appendChild(row);
      return;
    }

    const events = stateObj.attributes && stateObj.attributes.events;
    if (!Array.isArray(events) || events.length === 0) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = strings.emptyEvents;
      this._content.appendChild(row);
      return;
    }

    events.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "event";

      const name = document.createElement("div");
      name.className = "name";
      name.textContent = entry.name || "";

      const meta = document.createElement("div");
      meta.className = "meta";
      const metaParts = [];
      if (entry.gdate_cy_weekday) {
        metaParts.push(entry.gdate_cy_weekday);
      } else if (entry.gdate_cy) {
        metaParts.push(entry.gdate_cy);
      }
      if (entry.hdate) {
        metaParts.push(entry.hdate);
      }
      if (entry.hdate_he) {
        metaParts.push(entry.hdate_he);
      }
      meta.textContent = metaParts.join(" - ");

      row.appendChild(name);
      row.appendChild(meta);
      this._content.appendChild(row);
    });
  }

  getCardSize() {
    if (!this._config || !this._config.entity || !this._content) {
      return 1;
    }
    const rows = this._content.querySelectorAll(".event").length;
    return Math.max(1, rows + 1);
  }
}

if (!customElements.get("hmemorial-card")) {
  customElements.define("hmemorial-card", HmemorialCard);
}

class HmemorialBirthdayCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("entity is required");
    }

    this._config = {
      title: null,
      ...config,
    };

    if (!this._card) {
      this._card = document.createElement("ha-card");
      this._content = document.createElement("div");
      this._content.className = "card-content";
      this._card.appendChild(this._content);

      const style = document.createElement("style");
      style.textContent = `
        .card-content {
          padding: 8px 16px 12px 16px;
        }
        .birthday {
          margin: 8px 0;
        }
        .empty {
          color: var(--secondary-text-color);
          padding: 8px 0;
        }
      `;
      this._card.appendChild(style);
      this.appendChild(this._card);
    }
  }

  set hass(hass) {
    if (!this._config) {
      return;
    }

    const stateObj = hass.states[this._config.entity];
    const lang = hmGetLang(this._config, hass);
    const strings = HM_I18N[lang] || HM_I18N.en;
    const title =
      this._config.title ||
      (stateObj && stateObj.attributes && stateObj.attributes.friendly_name) ||
      strings.birthdayTitle;

    this._card.header = title;
    this._card.setAttribute("dir", lang === "he" ? "rtl" : "ltr");
    this._content.innerHTML = "";

    if (!stateObj) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = hmT(lang, "notFound", { entity: this._config.entity });
      this._content.appendChild(row);
      return;
    }

    const events = stateObj.attributes && stateObj.attributes.events;
    if (!Array.isArray(events) || events.length === 0) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = strings.emptyBirthdays;
      this._content.appendChild(row);
      return;
    }

    const today = new Date();
    const todayY = today.getFullYear();
    const todayM = today.getMonth();
    const todayD = today.getDate();

    events.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "birthday";

      const nameText = entry.name || "";
      const ageText =
        this._config.show_age && typeof entry.age === "number"
          ? ` (${entry.age}${strings.yearsSuffix})`
          : "";

      const strong = document.createElement("strong");
      strong.textContent = `${nameText}${ageText}`;

      let eventDate = null;
      if (entry.gdate_cy) {
        eventDate = new Date(`${entry.gdate_cy}T00:00:00`);
      }

      const isToday =
        eventDate &&
        eventDate.getFullYear() === todayY &&
        eventDate.getMonth() === todayM &&
        eventDate.getDate() === todayD;

      let weekday = hmWeekdayLabel(eventDate, lang);
      if (!weekday && entry.gdate_cy_weekday) {
        weekday = entry.gdate_cy_weekday;
      }

      const sentence = document.createElement("span");
      if (isToday) {
        sentence.textContent = ` ${hmT(lang, "birthdayTodaySuffix")}`;
      } else if (weekday) {
        sentence.textContent = ` ${hmT(lang, "birthdayOnSuffix", { weekday })}`;
      } else {
        sentence.textContent = ` ${hmT(lang, "birthdayDefaultSuffix")}`;
      }

      row.appendChild(strong);
      row.appendChild(sentence);
      this._content.appendChild(row);
    });
  }

  getCardSize() {
    if (!this._config || !this._config.entity || !this._content) {
      return 1;
    }
    const rows = this._content.querySelectorAll(".birthday").length;
    return Math.max(1, rows + 1);
  }
}

if (!customElements.get("hmemorial-birthday-card")) {
  customElements.define("hmemorial-birthday-card", HmemorialBirthdayCard);
}

window.customCards = window.customCards || [];
const hmemorialCard = window.customCards.find(
  (card) => card.type === "hmemorial-card",
);
if (!hmemorialCard) {
  window.customCards.push({
    type: "hmemorial-card",
    name: "HMemorial",
    description: "Hebrew memorial events and birthdays",
  });
}

const hmemorialBirthdayCard = window.customCards.find(
  (card) => card.type === "hmemorial-birthday-card",
);
if (!hmemorialBirthdayCard) {
  window.customCards.push({
    type: "hmemorial-birthday-card",
    name: "HMemorial Birthday",
    description: "Birthday summary card",
  });
}
