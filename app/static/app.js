document.addEventListener("DOMContentLoaded", () => {
  const addRowBtn = document.getElementById("add-ing-row");
  if (addRowBtn) {
    addRowBtn.addEventListener("click", () => {
      const container = document.getElementById("ingredient-rows");
      const row = document.createElement("div");
      row.className = "ing-row";
      row.innerHTML = `
        <input type="text" name="ing_name" placeholder="Ingredient name">
        <input type="text" name="ing_qty" placeholder="Qty">
        <input type="text" name="ing_unit" placeholder="Unit">
      `;
      container.appendChild(row);
    });
  }

  const loadOnlineBtn = document.getElementById("load-online");
  if (loadOnlineBtn) {
    loadOnlineBtn.addEventListener("click", async () => {
      const resultsEl = document.getElementById("online-results");
      const statusEl = document.getElementById("online-status");
      resultsEl.innerHTML = "";
      statusEl.textContent = "Searching...";
      try {
        const resp = await fetch("/recommendations/online");
        const data = await resp.json();
        if (!resp.ok) {
          statusEl.textContent = data.error || "Something went wrong.";
          return;
        }
        statusEl.textContent = "";
        if (!data.results.length) {
          statusEl.textContent = "No matching recipes found.";
          return;
        }
        for (const r of data.results) {
          const card = document.createElement("a");
          card.className = "recipe-card";
          card.href = r.url;
          card.target = "_blank";
          card.rel = "noopener";
          const caloriesText = r.calories
            ? `${Math.round(r.calories)} kcal / serving`
            : "Calories unavailable";
          card.innerHTML = `
            <h3></h3>
            <p></p>
            <p class="calories"></p>
          `;
          card.querySelector("h3").textContent = r.title;
          card.querySelectorAll("p")[0].textContent = `${r.used_count} on hand, ${r.missed_count} missing`;
          card.querySelectorAll("p")[1].textContent = caloriesText;
          if (r.missing.length) {
            const missingP = document.createElement("p");
            missingP.className = "missing";
            missingP.textContent = `Missing: ${r.missing.join(", ")}`;
            card.appendChild(missingP);
          }
          resultsEl.appendChild(card);
        }
      } catch (e) {
        statusEl.textContent = "Network error contacting the server.";
      }
    });
  }
});
