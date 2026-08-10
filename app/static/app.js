// Keep in sync with UNIT_OPTIONS in app/templates_config.py
const UNIT_OPTIONS = [
  "g", "kg", "ml", "l", "tsp", "tbsp", "cup", "oz", "lb",
  "pinch", "dash", "clove", "slice", "can", "jar", "bottle",
  "bag", "box", "packet", "bunch", "piece",
];

window.toggleUnitOther = (select) => {
  const otherInput = select.parentElement.querySelector(".unit-other");
  if (!otherInput) return;
  if (select.value === "other") {
    otherInput.style.display = "inline-block";
  } else {
    otherInput.style.display = "none";
    otherInput.value = "";
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const addRowBtn = document.getElementById("add-ing-row");
  if (addRowBtn) {
    addRowBtn.addEventListener("click", () => {
      const container = document.getElementById("ingredient-rows");
      const row = document.createElement("div");
      row.className = "ing-row";
      const unitOptionsHtml = UNIT_OPTIONS.map((u) => `<option value="${u}">${u}</option>`).join("");
      row.innerHTML = `
        <input type="text" name="ing_name" placeholder="Ingredient name">
        <input type="text" name="ing_qty" placeholder="Qty">
        <select name="ing_unit" class="unit-select" onchange="window.toggleUnitOther(this)">
          <option value="" selected>unit&hellip;</option>
          ${unitOptionsHtml}
          <option value="other">Other&hellip;</option>
        </select>
        <input type="text" name="ing_unit_other" class="unit-other" placeholder="Custom unit" style="display: none;">
      `;
      container.appendChild(row);
    });
  }

  const calorieCalcRoot = document.getElementById("calorie-calc");
  if (calorieCalcRoot) {
    const servings = parseFloat(calorieCalcRoot.dataset.servings) || 1;
    const totalDisplay = document.getElementById("calc-total-calories");
    const perServingDisplay = document.getElementById("calc-per-serving-display");
    const perServingInput = document.getElementById("per-serving-input");

    const round1 = (n) => Math.round(n * 10) / 10;

    const recalculate = () => {
      const inputs = calorieCalcRoot.querySelectorAll(".ing-calorie-input");
      let total = 0;
      inputs.forEach((input) => {
        const val = parseFloat(input.value);
        total += isNaN(val) ? 0 : val;
      });
      const perServing = round1(total / servings);
      totalDisplay.textContent = round1(total);
      perServingDisplay.textContent = perServing;
      perServingInput.value = perServing;
    };

    calorieCalcRoot.querySelectorAll(".ing-calorie-input").forEach((input) => {
      input.addEventListener("input", recalculate);
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
            const missingLabel = document.createElement("p");
            missingLabel.className = "missing-label";
            missingLabel.textContent = "Missing:";
            card.appendChild(missingLabel);

            const missingList = document.createElement("ul");
            missingList.className = "missing-list";
            for (const name of r.missing) {
              const li = document.createElement("li");
              li.textContent = name;
              missingList.appendChild(li);
            }
            card.appendChild(missingList);
          }
          resultsEl.appendChild(card);
        }
      } catch (e) {
        statusEl.textContent = "Network error contacting the server.";
      }
    });
  }
});
