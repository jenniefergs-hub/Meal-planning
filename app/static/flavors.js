document.addEventListener("DOMContentLoaded", () => {
  const lookupBtn = document.getElementById("lookup-btn");
  const lookupInput = document.getElementById("lookup-input");
  const lookupStatus = document.getElementById("lookup-status");
  const lookupResults = document.getElementById("lookup-results");

  function renderPairingCards(container, pairs) {
    container.innerHTML = "";
    for (const p of pairs) {
      const card = document.createElement("div");
      card.className = "pairing-card";
      const strong = document.createElement("strong");
      strong.textContent = p.name;
      const note = document.createElement("p");
      note.textContent = p.reason;
      card.appendChild(strong);
      card.appendChild(note);
      container.appendChild(card);
    }
  }

  async function runLookup() {
    const value = lookupInput.value.trim();
    lookupResults.innerHTML = "";
    if (!value) {
      lookupStatus.textContent = "Enter an ingredient first.";
      return;
    }
    lookupStatus.textContent = "Looking up...";
    try {
      const resp = await fetch(`/flavors/api/pairings?ingredient=${encodeURIComponent(value)}`);
      const data = await resp.json();
      if (!resp.ok) {
        lookupStatus.textContent = data.error || "Something went wrong.";
        return;
      }
      lookupStatus.textContent = `Pairs well with (${data.category}):`;
      renderPairingCards(lookupResults, data.pairs);
    } catch (e) {
      lookupStatus.textContent = "Network error contacting the server.";
    }
  }

  if (lookupBtn) {
    lookupBtn.addEventListener("click", runLookup);
    lookupInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runLookup();
    });
  }

  const comboBtn = document.getElementById("combo-btn");
  const comboInput = document.getElementById("combo-input");
  const comboStatus = document.getElementById("combo-status");
  const comboResults = document.getElementById("combo-results");

  async function runCombo() {
    const value = comboInput.value.trim();
    comboResults.innerHTML = "";
    if (!value) {
      comboStatus.textContent = "Enter at least two ingredients.";
      return;
    }
    comboStatus.textContent = "Checking...";
    try {
      const resp = await fetch(`/flavors/api/combo?ingredients=${encodeURIComponent(value)}`);
      const data = await resp.json();
      if (!resp.ok) {
        comboStatus.textContent = data.error || "Something went wrong.";
        return;
      }
      comboStatus.textContent = "";
      if (data.unresolved.length) {
        const warn = document.createElement("p");
        warn.className = "hint";
        warn.textContent = `Not in the flavor dataset, skipped: ${data.unresolved.join(", ")}`;
        comboResults.appendChild(warn);
      }

      if (data.pairwise.length) {
        const h3 = document.createElement("h3");
        h3.textContent = "Compatibility";
        comboResults.appendChild(h3);
        const grid = document.createElement("div");
        grid.className = "pairing-grid";
        for (const pw of data.pairwise) {
          const card = document.createElement("div");
          card.className = "pairing-card" + (pw.compatible ? "" : " pairing-card-neutral");
          const strong = document.createElement("strong");
          strong.textContent = `${pw.a} + ${pw.b}`;
          const note = document.createElement("p");
          note.textContent = pw.compatible
            ? pw.reason
            : "No classic pairing on record — not necessarily a bad combo, just untested here.";
          card.appendChild(strong);
          card.appendChild(note);
          grid.appendChild(card);
        }
        comboResults.appendChild(grid);
      }

      const h3b = document.createElement("h3");
      h3b.textContent = "Pairs with all of them";
      comboResults.appendChild(h3b);
      if (data.suggestions.length) {
        const grid = document.createElement("div");
        grid.className = "pairing-grid";
        for (const s of data.suggestions) {
          const card = document.createElement("div");
          card.className = "pairing-card";
          const strong = document.createElement("strong");
          strong.textContent = s.name;
          const note = document.createElement("p");
          note.textContent = s.reasons[0];
          card.appendChild(strong);
          card.appendChild(note);
          grid.appendChild(card);
        }
        comboResults.appendChild(grid);
      } else {
        const p = document.createElement("p");
        p.className = "hint";
        p.textContent = "Nothing in the dataset pairs with all of these at once.";
        comboResults.appendChild(p);
      }
    } catch (e) {
      comboStatus.textContent = "Network error contacting the server.";
    }
  }

  if (comboBtn) {
    comboBtn.addEventListener("click", runCombo);
    comboInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runCombo();
    });
  }
});
