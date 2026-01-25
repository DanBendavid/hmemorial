class HmemorialCard extends HTMLElement {
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
    const title =
      this._config.title ||
      (stateObj && stateObj.attributes && stateObj.attributes.friendly_name) ||
      "Hmemorial";

    this._card.header = title;
    this._content.innerHTML = "";

    if (!stateObj) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = `Entity not found: ${this._config.entity}`;
      this._content.appendChild(row);
      return;
    }

    const events = stateObj.attributes && stateObj.attributes.events;
    if (!Array.isArray(events) || events.length === 0) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = "Aucun evenement";
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
      title: "Anniversaires",
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
    const title =
      this._config.title ||
      (stateObj && stateObj.attributes && stateObj.attributes.friendly_name) ||
      "Anniversaires";

    this._card.header = title;
    this._content.innerHTML = "";

    if (!stateObj) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = `Entity not found: ${this._config.entity}`;
      this._content.appendChild(row);
      return;
    }

    const events = stateObj.attributes && stateObj.attributes.events;
    if (!Array.isArray(events) || events.length === 0) {
      const row = document.createElement("div");
      row.className = "empty";
      row.textContent = "Aucun anniversaire cette semaine.";
      this._content.appendChild(row);
      return;
    }

    const jours = {
      Monday: "lundi",
      Tuesday: "mardi",
      Wednesday: "mercredi",
      Thursday: "jeudi",
      Friday: "vendredi",
      Saturday: "samedi",
      Sunday: "dimanche",
    };

    const today = new Date();
    const todayY = today.getFullYear();
    const todayM = today.getMonth();
    const todayD = today.getDate();

    events.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "birthday";

      const nameText = entry.name || "";
      const ageText =
        typeof entry.age === "number" ? ` (${entry.age} ans)` : "";

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

      let weekday = null;
      if (eventDate && !isNaN(eventDate)) {
        const weekdayEn = eventDate.toLocaleDateString("en-US", {
          weekday: "long",
        });
        weekday = jours[weekdayEn] || weekdayEn;
      } else if (entry.gdate_cy_weekday) {
        weekday = entry.gdate_cy_weekday;
      }

      const sentence = document.createElement("span");
      if (isToday) {
        sentence.textContent = " fete son anniversaire aujourd'hui.";
      } else if (weekday) {
        sentence.textContent = ` fete son anniversaire ce ${weekday}.`;
      } else {
        sentence.textContent = " fete son anniversaire.";
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
