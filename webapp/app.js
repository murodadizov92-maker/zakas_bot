const IS_TELEGRAM = !!(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData);
const tg = window.Telegram ? window.Telegram.WebApp : null;

if (IS_TELEGRAM) {
  tg.ready();
  tg.expand();
} else {
  document.getElementById("web-info").classList.remove("hidden");
}

let CATALOG = {};
let ORDER_OPEN = true;
let ACTIVE_CATEGORY = null;

// cart: { [productId]: { qty: number, unit: 'kg' | 'dona', name, price } }
const cart = {};

const el = (id) => document.getElementById(id);

async function loadProducts() {
  const res = await fetch("/api/products");
  const data = await res.json();
  CATALOG = data.catalog;
  ORDER_OPEN = data.order_open;

  if (!ORDER_OPEN) {
    el("open-time").textContent = data.open_from;
    el("cutoff-time").textContent = data.cutoff;
    el("closed-banner").classList.remove("hidden");
  }

  const categories = Object.keys(CATALOG);
  ACTIVE_CATEGORY = categories[0];
  updateSearchPlaceholder();
  renderCategories(categories);
  renderProducts();
}

function updateSearchPlaceholder() {
  el("search").placeholder = ACTIVE_CATEGORY
    ? `${ACTIVE_CATEGORY} ichidan qidirish...`
    : "Mahsulot qidirish...";
}

function renderCategories(categories) {
  const wrap = el("categories");
  wrap.innerHTML = "";
  categories.forEach((cat) => {
    const chip = document.createElement("button");
    chip.className = "cat-chip" + (cat === ACTIVE_CATEGORY ? " active" : "");
    chip.textContent = cat;
    chip.onclick = () => {
      ACTIVE_CATEGORY = cat;
      document.querySelectorAll(".cat-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      updateSearchPlaceholder();
      renderProducts();
    };
    wrap.appendChild(chip);
  });
}

function renderProducts() {
  const container = el("products");
  container.innerHTML = "";
  const query = el("search").value.trim().toLowerCase();

  // Qidiruv faqat tanlangan kategoriya ichida ishlaydi
  const items = (CATALOG[ACTIVE_CATEGORY] || []).filter(
    (p) => !query || p.name.toLowerCase().includes(query)
  );

  const title = document.createElement("div");
  title.className = "cat-group-title";
  title.textContent = ACTIVE_CATEGORY;
  container.appendChild(title);

  if (items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "product-price";
    empty.style.padding = "12px 4px";
    empty.textContent = "Bu kategoriyada topilmadi";
    container.appendChild(empty);
    return;
  }

  items.forEach((p) => container.appendChild(renderProductRow(p)));
}

function renderProductRow(product) {
  const row = document.createElement("div");
  row.className = "product-row";
  row.id = `row-${product.id}`;

  const existing = cart[product.id];
  if (existing) row.classList.add("filled");

  row.innerHTML = `
    <div class="product-name">${product.name}</div>
    <div class="product-price">${formatPrice(product.price)} so'm</div>
    <div class="qty-row">
      <div class="unit-toggle">
        <button type="button" data-unit="kg" class="${(!existing || existing.unit === 'kg') ? 'active' : ''}">kg</button>
        <button type="button" data-unit="dona" class="${(existing && existing.unit === 'dona') ? 'active' : ''}">dona</button>
      </div>
      <input class="qty-input" type="number" inputmode="decimal" min="0" step="0.1"
             placeholder="0" value="${existing ? existing.qty : ''}">
    </div>
  `;

  const unitBtns = row.querySelectorAll(".unit-toggle button");
  const qtyInput = row.querySelector(".qty-input");
  let currentUnit = existing ? existing.unit : "kg";

  unitBtns.forEach((btn) => {
    btn.onclick = () => {
      currentUnit = btn.dataset.unit;
      unitBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      updateCartItem(product, qtyInput.value, currentUnit, row);
    };
  });

  qtyInput.oninput = () => {
    updateCartItem(product, qtyInput.value, currentUnit, row);
  };

  return row;
}

function updateCartItem(product, qtyStr, unit, row) {
  const qty = parseFloat(qtyStr);
  if (!qty || qty <= 0) {
    delete cart[product.id];
    row.classList.remove("filled");
  } else {
    cart[product.id] = { qty, unit, name: product.name, price: product.price };
    row.classList.add("filled");
  }
  updateCartBar();
}

function updateCartBar() {
  const count = Object.keys(cart).length;
  const bar = el("cart-bar");
  el("cart-count").textContent = count;
  bar.classList.toggle("hidden", count === 0);
}

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function showToast(msg) {
  const t = el("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2500);
}

// ---------- review screen ----------

function renderReview() {
  const list = el("review-list");
  list.innerHTML = "";
  let totalKg = 0, totalDona = 0;

  Object.entries(cart).forEach(([id, item]) => {
    if (item.unit === "kg") totalKg += item.qty; else totalDona += item.qty;
    const row = document.createElement("div");
    row.className = "review-item";
    row.innerHTML = `
      <span>${item.name} — ${item.qty} ${item.unit === 'kg' ? 'kg' : 'dona'}</span>
      <button class="remove-btn" data-id="${id}">✕</button>
    `;
    row.querySelector(".remove-btn").onclick = () => {
      delete cart[id];
      renderReview();
      updateCartBar();
      const domRow = el(`row-${id}`);
      if (domRow) {
        domRow.classList.remove("filled");
        const input = domRow.querySelector(".qty-input");
        if (input) input.value = "";
      }
    };
    list.appendChild(row);
  });

  const parts = [];
  if (totalKg > 0) parts.push(`${totalKg.toFixed(2).replace(/\.?0+$/,'')} kg`);
  if (totalDona > 0) parts.push(`${totalDona} dona`);
  el("review-total").textContent = "Jami: " + (parts.join(", ") || "0");
}

el("review-btn").onclick = () => {
  if (Object.keys(cart).length === 0) return;
  renderReview();
  el("review-screen").classList.remove("hidden");
};

el("back-btn").onclick = () => {
  el("review-screen").classList.add("hidden");
};

el("submit-btn").onclick = async () => {
  if (!ORDER_OPEN) {
    showToast("Buyurtma qabul qilish vaqti tugagan");
    return;
  }

  const items = Object.entries(cart).map(([id, item]) => ({
    id: parseInt(id),
    qty: item.qty,
    unit: item.unit,
  }));
  if (items.length === 0) return;

  const payload = { items };

  if (IS_TELEGRAM) {
    payload.initData = tg.initData;
  } else {
    const webName = el("web-name").value.trim();
    const webPhone = el("web-phone").value.trim();
    if (!webName || !webPhone) {
      showToast("Ism va telefon raqamingizni kiriting");
      return;
    }
    payload.webName = webName;
    payload.webPhone = webPhone;
  }

  el("submit-btn").disabled = true;
  el("submit-btn").textContent = "Yuborilmoqda...";

  try {
    const res = await fetch("/api/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.ok) {
      if (IS_TELEGRAM) tg.HapticFeedback?.notificationOccurred("success");
      showToast("✅ Buyurtma yuborildi!");
      setTimeout(() => {
        if (IS_TELEGRAM) tg.close();
      }, 1200);
    } else if (data.error === "closed") {
      showToast("⏰ Buyurtma vaqti tugagan");
    } else if (data.error === "missing_info") {
      showToast("Ism va telefon raqamingizni kiriting");
    } else {
      showToast("Xatolik yuz berdi, qayta urinib ko'ring");
    }
  } catch (e) {
    showToast("Tarmoq xatoligi");
  } finally {
    el("submit-btn").disabled = false;
    el("submit-btn").textContent = "✅ Tasdiqlash va yuborish";
  }
};

el("search").addEventListener("input", renderProducts);

loadProducts();
