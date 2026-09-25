const API_BASE_URL = "http://127.0.0.1:8003";

const $ = id => document.getElementById(id);

async function api(path, options = {}) {
  const r = await fetch(API_BASE_URL + path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  let d = {};
  try {
    d = await r.json();
  } catch {}

  if (!r.ok) {
    throw new Error(d.detail || `API error ${r.status}`);
  }

  return d;
}

function esc(v) {
  return String(v ?? "").replace(
    /[&<>"']/g,
    m => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[m])
  );
}


/* =========================================================
   ORDER STATUS FLOW
   ========================================================= */

const FLOW = [
  "PENDING",
  "ACCEPTED",
  "IN PRODUCTION",
  "READY",
  "DISPATCHED",
  "DELIVERED"
];


/* =========================================================
   ROLE CHECK
   ========================================================= */

function getUserRole() {
  return localStorage.getItem("userRole") || "";
}


/* =========================================================
   FACTORY ONLY - NEXT STEP BUTTON
   ========================================================= */

function statusButton(order) {

  const role = getUserRole();

  /*
    Retailer:
    ONLY VIEW STATUS.
    No Accept / Production / Dispatch / Deliver buttons.
  */
  if (role !== "factory") {
    return `
      <span class="status-view">
        ${esc(order.status)}
      </span>
    `;
  }


  /*
    Factory:
    Factory can move the order to the next stage.
  */

  const i = FLOW.indexOf(order.status);
  const next = FLOW[i + 1];

  if (next) {
    return `
      <button
        class="primary-btn small-btn"
        onclick="advanceOrder('${esc(order.order_id)}','${next}')"
      >
        ${next}
      </button>
    `;
  }

  return `
    <span class="status-ok">
      Delivered
    </span>
  `;
}


/* =========================================================
   LOAD ORDERS
   ========================================================= */

async function loadOrders(target = "orders") {

  try {

    const d = await api("/api/purchase-orders");

    const el = $(target);

    if (!el) return;


    if (!d.orders.length) {

      el.innerHTML = `
        <p>No purchase orders yet.</p>
      `;

      return;
    }


    const role = getUserRole();


    /*
      RETAILER VIEW
      -------------------------
      Only:
      Order
      Product
      Quantity
      Factory
      Status

      NO NEXT STEP / ACTION
    */

    if (role === "retailer") {

      el.innerHTML = `
        <div class="table-wrap">

          <table>

            <thead>
              <tr>
                <th>Order</th>
                <th>Product</th>
                <th>Qty</th>
                <th>Factory</th>
                <th>Order Status</th>
              </tr>
            </thead>

            <tbody>

              ${d.orders.map(o => `
                <tr>

                  <td>
                    ${esc(o.order_id)}
                  </td>

                  <td>
                    ${esc(o.product)}
                  </td>

                  <td>
                    ${o.quantity}
                  </td>

                  <td>
                    ${esc(o.factory)}
                  </td>

                  <td>
                    <strong>
                      ${esc(o.status)}
                    </strong>
                  </td>

                </tr>
              `).join("")}

            </tbody>

          </table>

        </div>
      `;

      return;
    }


    /*
      FACTORY VIEW
      -------------------------
      Factory can see Next Step.
    */

    if (role === "factory") {

      el.innerHTML = `
        <div class="table-wrap">

          <table>

            <thead>
              <tr>
                <th>Order</th>
                <th>Product</th>
                <th>Qty</th>
                <th>Factory</th>
                <th>Status</th>
                <th>Next Step</th>
              </tr>
            </thead>

            <tbody>

              ${d.orders.map(o => `
                <tr>

                  <td>
                    ${esc(o.order_id)}
                  </td>

                  <td>
                    ${esc(o.product)}
                  </td>

                  <td>
                    ${o.quantity}
                  </td>

                  <td>
                    ${esc(o.factory)}
                  </td>

                  <td>
                    <strong>
                      ${esc(o.status)}
                    </strong>
                  </td>

                  <td>
                    ${statusButton(o)}
                  </td>

                </tr>
              `).join("")}

            </tbody>

          </table>

        </div>
      `;

      return;
    }


    /*
      OTHER ROLES
      -------------------------
      Show orders without actions.
    */

    el.innerHTML = `
      <div class="table-wrap">

        <table>

          <thead>
            <tr>
              <th>Order</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Factory</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>

            ${d.orders.map(o => `
              <tr>
                <td>${esc(o.order_id)}</td>
                <td>${esc(o.product)}</td>
                <td>${o.quantity}</td>
                <td>${esc(o.factory)}</td>
                <td><strong>${esc(o.status)}</strong></td>
              </tr>
            `).join("")}

          </tbody>

        </table>

      </div>
    `;

  } catch (e) {

    if ($(target)) {
      $(target).innerHTML =
        `<p class="error">${esc(e.message)}</p>`;
    }

  }
}


/* =========================================================
   ADVANCE ORDER
   FACTORY ONLY
   ========================================================= */

async function advanceOrder(id, status) {

  /*
    SECURITY CHECK ON FRONTEND
    Retailer cannot use this function.
  */

  if (getUserRole() !== "factory") {

    alert("Only Factory can update order status.");

    return;
  }


  try {

    const d = await api(
      `/api/purchase-orders/${encodeURIComponent(id)}/status`,
      {
        method: "PUT",

        body: JSON.stringify({
          status: status
        })
      }
    );


    alert(
      `${status} recorded. ${d.production?.recommendation || ""}`
    );


    await loadOrders("orders");
    await loadOrders("factoryOrders");
    await loadFactoryData();

  } catch (e) {

    alert(e.message);

  }
}


/* =========================================================
   FACTORY DATA
   ========================================================= */

async function loadFactoryData() {

  try {

    const [
      cap,
      raw,
      prod,
      disp
    ] = await Promise.all([

      api("/api/factory/capacity"),

      api("/api/factory/raw-materials"),

      api("/api/factory/production-data"),

      api("/api/factory/dispatch-data")

    ]);


    if ($("factoryData")) {

      $("factoryData").innerHTML = `

        <h3>Capacity</h3>

        <div class="table-wrap">

          <table>

            <tr>
              <th>Factory</th>
              <th>Location</th>
              <th>Capacity</th>
              <th>Available</th>
            </tr>

            ${cap.data.slice(0, 6).map(x => `

              <tr>

                <td>
                  ${esc(x.factory_name)}
                </td>

                <td>
                  ${esc(x.location)}
                </td>

                <td>
                  ${x.total_capacity}
                </td>

                <td>
                  ${x.available_capacity}
                </td>

              </tr>

            `).join("")}

          </table>

        </div>


        <h3>Raw Materials</h3>

        <div class="table-wrap">

          <table>

            <tr>
              <th>Material</th>
              <th>Stock</th>
              <th>Reorder Level</th>
              <th>Status</th>
            </tr>

            ${raw.data.slice(0, 8).map(x => `

              <tr>

                <td>
                  ${esc(x.material_name)}
                </td>

                <td>
                  ${x.current_stock}
                  ${esc(x.unit)}
                </td>

                <td>
                  ${x.reorder_level}
                </td>

                <td>

                  ${
                    Number(x.current_stock) <=
                    Number(x.reorder_level)

                    ? '<b class="error">REORDER</b>'

                    : '<span class="status-ok">SUFFICIENT</span>'
                  }

                </td>

              </tr>

            `).join("")}

          </table>

        </div>


        <h3>Production Records</h3>

        <p>
          ${prod.production_status.length}
          production status records loaded.

          Dispatch records:
          ${disp.dispatch.length}.
        </p>

      `;

    }

  } catch (e) {

    if ($("factoryData")) {

      $("factoryData").innerHTML =
        `<p class="error">${esc(e.message)}</p>`;

    }

  }
}


/* =========================================================
   FACTORY DASHBOARD
   ========================================================= */

async function loadFactory() {

  try {

    const d = await api("/api/purchase-orders");

    const orders = d.orders || [];


    if ($("newOrders")) {

      $("newOrders").textContent =
        orders.filter(
          o => o.status === "PENDING"
        ).length;

    }


    if ($("inProduction")) {

      $("inProduction").textContent =
        orders.filter(
          o => o.status === "IN PRODUCTION"
        ).length;

    }


    if ($("readyOrders")) {

      $("readyOrders").textContent =
        orders.filter(
          o =>
            [
              "READY",
              "DISPATCHED",
              "DELIVERED"
            ].includes(o.status)
        ).length;

    }


    await loadOrders("factoryOrders");

    await loadFactoryData();

  } catch (e) {

    console.error(e);

  }
}


/* =========================================================
   CUSTOMER DASHBOARD
   ========================================================= */

async function loadCustomer() {

  try {

    const [
      rec,
      products,
      history,
      notes
    ] = await Promise.all([

      api("/api/customer/recommendations"),

      api("/api/customer/products"),

      api("/api/customer/purchase-history"),

      api("/api/customer/notifications")

    ]);


    if ($("customerRecommendations")) {

      $("customerRecommendations").innerHTML =
        (rec.recommendations || [])
          .map(x => `

            <div class="recommendation-card">

              <h3>
                ${esc(x.product)}
              </h3>

              <p>
                ${esc(x.reason)}
              </p>

              <small>
                Recommendation score:
                ${x.score}
              </small>

            </div>

          `)
          .join("");

    }


    if ($("customerProducts")) {

      $("customerProducts").innerHTML =
        (products.products || [])
          .map(x => `

            <tr>

              <td>
                ${esc(x.product)}
              </td>

              <td>
                ${x.available_stock}
              </td>

              <td>
                ${Number(
                  x.predicted_daily_demand
                ).toFixed(1)}/day
              </td>

              <td>
                ${esc(x.risk)}
              </td>

              <td>

                ${
                  x.available

                    ? '<span class="status-ok">Available</span>'

                    : '<span class="error">Unavailable</span>'
                }

              </td>

            </tr>

          `)
          .join("");

    }


    if ($("customerHistory")) {

      $("customerHistory").innerHTML =
        (history.orders || [])
          .map(x => `

            <tr>

              <td>
                ${esc(x.order_id)}
              </td>

              <td>
                ${esc(x.product)}
              </td>

              <td>
                ${x.quantity}
              </td>

              <td>
                ${esc(x.status)}
              </td>

            </tr>

          `)
          .join("")
          ||
          '<tr><td colspan="4">No purchases yet.</td></tr>';

    }


    if ($("availabilityNotifications")) {

      $("availabilityNotifications").innerHTML =
        (notes.notifications || [])
          .map(x => `

            <div class="content-card">

              <b>
                ${esc(x.product)}
              </b>

              <p>
                ${esc(x.message)}
              </p>

            </div>

          `)
          .join("")
          ||
          "<p>No availability alerts.</p>";

    }

  } catch (e) {

    if ($("customerRecommendations")) {

      $("customerRecommendations").textContent =
        e.message;

    }

  }
}


/* =========================================================
   CUSTOMER FEEDBACK
   ========================================================= */

async function sendCustomerFeedback() {

  try {

    const d = await api(
      "/api/customer/feedback",
      {
        method: "POST",

        body: JSON.stringify({

          product: $("feedbackProduct").value,

          feedback: $("feedbackText").value,

          rating: Number(
            $("feedbackRating")?.value || 5
          )

        })

      }
    );


    $("customerFeedbackStatus").textContent =
      `Sentiment: ${d.sentiment} | Polarity: ${d.polarity}`;

  } catch (e) {

    $("customerFeedbackStatus").textContent =
      e.message;

  }
}


/* =========================================================
   PAGE INITIALIZATION
   ========================================================= */

if ($("orders")) {
  loadOrders("orders");
}

if ($("factoryOrders")) {
  loadFactory();
}

if ($("customerRecommendations")) {
  loadCustomer();
}
