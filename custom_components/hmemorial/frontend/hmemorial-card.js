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
