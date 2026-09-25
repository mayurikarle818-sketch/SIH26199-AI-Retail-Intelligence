const API_BASE_URL = "http://127.0.0.1:8003";


/* =========================
   PRODUCT SEARCH
========================= */

const productSearch =
    document.getElementById("productSearch");

if (productSearch) {

    productSearch.addEventListener("input", function () {

        const searchValue =
            productSearch.value.toLowerCase().trim();

        const rows =
            document.querySelectorAll(
                "#productTable tbody tr"
            );

        rows.forEach(row => {

            row.style.display =
                row.innerText
                    .toLowerCase()
                    .includes(searchValue)
                    ? ""
                    : "none";

        });

    });

}


/* =========================
   PRODUCT ACTIONS
========================= */

function showProductMessage() {

    alert(
        "Add Product is not enabled in this MVP."
    );

}


function takeAction(productName, quantity) {

    const confirmAction = confirm(

        "AI Recommendation\n\n" +

        "Product: " + productName +

        "\nRecommended Order: " +
        quantity +

        " units\n\n" +

        "Do you want to proceed with this action?"

    );

    if (confirmAction) {

        alert(
            "Action confirmed. Reorder request created for " +
            quantity +
            " units of " +
            productName +
            "."
        );

    }

}


function viewDetails(
    productName,
    currentStock,
    predictedDemand,
    action
) {

    alert(

        "AI Recommendation Details\n\n" +

        "Product: " +
        productName +

        "\n\nCurrent Stock: " +
        currentStock +
        " units\n" +

        "Predicted Demand: " +
        predictedDemand +
        " units\n" +

        "Recommended Action: " +
        action

    );

}


/* =========================
   AI FEEDBACK
========================= */

async function submitFeedback(feedbackValue) {

    if (
        typeof recommendationData === "undefined" ||
        !recommendationData
    ) {

        alert(
            "AI recommendation is not loaded yet."
        );

        return;
    }

    const feedbackMessage =
        document.getElementById(
            "feedbackMessage"
        );

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/feedback`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        product:
                            recommendationData.product,

                        store:
                            recommendationData.store,

                        feedback:
                            feedbackValue

                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Feedback submission failed"
            );

        }

        if (feedbackMessage) {

            feedbackMessage.textContent =
                "Thank you. Your feedback has been saved.";

            feedbackMessage.style.display =
                "block";

        }

    } catch (error) {

        console.error(
            "Feedback Error:",
            error
        );

        if (feedbackMessage) {

            feedbackMessage.textContent =
                "Unable to save feedback.";

            feedbackMessage.style.display =
                "block";

        }

    }

}


/* =========================
   PURCHASE ORDER
========================= */

async function placeRecommendedOrder(
    product,
    store,
    quantity
) {

    if (
        !confirm(
            `Create purchase order for ${quantity} units of ${product}?`
        )
    ) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/purchase-orders`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        product: product,

                        store: store,

                        quantity: quantity,

                        retailer:
                            "Retail Store 1",

                        factory:
                            "Factory A",

                        priority:
                            "HIGH"

                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Order creation failed"
            );

        }

        alert(
            `Order ${data.order.order_id} created successfully.`
        );

        window.location.href =
            "orders.html";

    } catch (error) {

        alert(error.message);

    }

}


/* =========================
   AUTH
========================= */

function checkAuthentication() {

    /*
       Authentication is currently
       handled as MVP/demo navigation.
    */

    return true;

}


function logout() {

    localStorage.removeItem("userRole");

    window.location.href =
        "index.html";

}


checkAuthentication();
/* =========================
   FINAL MVP LOGIN GUARD
=========================*/
(function(){
  const page=location.pathname.split('/').pop();
  if(!page || page==='index.html') return;
  const role=localStorage.getItem('userRole');
  if(!role){ location.href='index.html'; return; }
})();
