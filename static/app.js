/* =========================================================
   NirNaya
   Evidence-First Settlement Intelligence
   Frontend Application
========================================================= */


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    initializeIcons();

    initializeThemeToggle();

    initializeNavigation();

    initializeQuickSearch();

});


/* =========================================================
   ICONS
========================================================= */

function initializeIcons() {

    if (window.lucide) {
        lucide.createIcons();
    }

}


/* =========================================================
   THEME
========================================================= */

function initializeThemeToggle() {

    const themeToggle =
        document.getElementById("themeToggle");

    if (!themeToggle) {
        return;
    }


    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("light-mode");

        const isLightMode =
            document.body.classList.contains("light-mode");


        localStorage.setItem(
            "nirnaya-theme",
            isLightMode ? "light" : "dark"
        );


        updateThemeIcon(isLightMode);

    });


    const savedTheme =
        localStorage.getItem("nirnaya-theme");


    if (savedTheme === "light") {

        document.body.classList.add("light-mode");

        updateThemeIcon(true);

    }

}


/* =========================================================
   THEME ICON
========================================================= */

function updateThemeIcon(isLightMode) {

    const themeToggle =
        document.getElementById("themeToggle");

    if (!themeToggle) {
        return;
    }


    themeToggle.innerHTML = isLightMode
        ? '<i data-lucide="moon"></i>'
        : '<i data-lucide="sun"></i>';


    initializeIcons();

}


/* =========================================================
   NAVIGATION
========================================================= */

/* =========================================================
   NAVIGATION
========================================================= */

function initializeNavigation() {

    const navItems =
        document.querySelectorAll(".nav-item");

    const overviewPage =
        document.getElementById("overviewPage");

    const investigationPage =
        document.getElementById("investigationPage");

    const backToOverview =
        document.getElementById("backToOverview");


    navItems.forEach((item) => {

        item.addEventListener("click", (event) => {

            event.preventDefault();

            const page =
                item.dataset.page;


            navItems.forEach((navItem) => {
                navItem.classList.remove("active");
            });

            item.classList.add("active");


            if (page === "investigation") {

                if (overviewPage) {
                    overviewPage.style.display = "none";
                }

                if (investigationPage) {
                    investigationPage.style.display = "block";
                }

                loadInvestigation();

            } else {

                if (investigationPage) {
                    investigationPage.style.display = "none";
                }

                if (overviewPage) {
                    overviewPage.style.display = "block";
                }

            }

        });

    });


    if (backToOverview) {

        backToOverview.addEventListener("click", () => {

            if (investigationPage) {
                investigationPage.style.display = "none";
            }

            if (overviewPage) {
                overviewPage.style.display = "block";
            }


            navItems.forEach((item) => {

                item.classList.remove("active");

                if (item.dataset.page === "overview") {
                    item.classList.add("active");
                }

            });

        });

    }

}


/* =========================================================
   QUICK SEARCH
========================================================= */

function initializeQuickSearch() {

    const input =
        document.getElementById("investigationInput");


    const quickButtons =
        document.querySelectorAll(".quick-searches button");


    if (!input) {
        return;
    }


    quickButtons.forEach((button) => {

        button.addEventListener("click", () => {

            input.value =
                button.textContent.trim();

            input.focus();

        });

    });

}
/* =========================================================
   LOAD REAL INVESTIGATION FROM BACKEND
========================================================= */

async function loadInvestigation(transactionId = "TXN_10021") {

    try {

        const response = await fetch(
            "/api/investigate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    transaction_id: transactionId
                })
            }
        );


        if (!response.ok) {
            throw new Error(
                `Backend error: ${response.status}`
            );
        }


        const result = await response.json();


        renderInvestigation(result);

    } catch (error) {

        console.error(
            "Investigation loading failed:",
            error
        );

    }

}


/* =========================================================
   RENDER REAL INVESTIGATION RESULT
========================================================= */

function renderInvestigation(result) {

    /* ---------------------------------------------
       BASIC TRANSACTION DATA
    --------------------------------------------- */

    setText(
        "investigationTransactionId",
        result.transaction_id || "Unavailable"
    );

    setText(
        "investigationSettlementId",
        result.settlement?.settlement_id || "Unavailable"
    );

    setText(
        "investigationAmount",
        result.amount != null
            ? formatCurrency(result.amount)
            : "Unavailable"
    );

    setText(
        "investigationCurrency",
        result.currency || "Unavailable"
    );


    /* ---------------------------------------------
       DETERMINATION
    --------------------------------------------- */

    setText(
        "investigationStatus",
        result.determination?.status || "EXCEPTION"
    );

    setText(
        "rootCause",
        result.determination?.root_cause
            ? formatRootCause(result.determination.root_cause)
            : "Unavailable"
    );

    setText(
        "severityText",
        result.determination?.severity
            ? `${result.determination.severity} severity`
            : "Severity unavailable"
    );


    /* ---------------------------------------------
       CONFIDENCE
    --------------------------------------------- */

    setText(
        "confidenceScore",
        result.confidence != null
            ? `${result.confidence}%`
            : "Unavailable"
    );


    /* ---------------------------------------------
       SOURCE STATUS
    --------------------------------------------- */

    setText(
        "gatewayStatus",
        formatStatus(result.gateway?.status)
    );

    setText(
        "gatewayAmount",
        result.gateway?.amount != null
            ? formatCurrency(result.gateway.amount)
            : "Unavailable"
    );

    setText(
        "gatewayTimestamp",
        formatTime(result.gateway?.timestamp)
    );


    setText(
        "bankStatus",
        formatStatus(result.bank?.status)
    );

    setText(
        "bankUtr",
        result.bank?.utr || "Unavailable"
    );


    setText(
        "ledgerStatus",
        formatStatus(result.ledger?.status)
    );

    setText(
        "ledgerAmount",
        result.ledger?.amount != null
            ? formatCurrency(result.ledger.amount)
            : "Unavailable"
    );


    /* ---------------------------------------------
       EVIDENCE
    --------------------------------------------- */

    renderEvidence(
        result.evidence || []
    );


    /* ---------------------------------------------
       EXCEPTIONS
    --------------------------------------------- */

    renderExceptions(
        result.exceptions || []
    );


    /* ---------------------------------------------
       RECOMMENDED ACTION
    --------------------------------------------- */

    setText(
        "recommendedAction",
        result.recommended_action || "No action available."
    );


    /* ---------------------------------------------
       TIMELINE
       Backend currently does not return timeline.
    --------------------------------------------- */

    const timelineContainer =
        document.getElementById(
            "investigationTimeline"
        );

    if (timelineContainer) {

        timelineContainer.innerHTML = `
            <div class="timeline-empty">
                Timeline data is currently unavailable.
            </div>
        `;

    }


    initializeIcons();

}
/* =========================================================
   MOCK INVESTIGATION RESULT
   Temporary frontend development data only.
========================================================= */

const mockInvestigationResult = {

    transaction_id: "TXN-10482",

    amount: 12500,

    currency: "INR",

    settlement: {

        settlement_id: "SET-78231",

        status: "processed",

        utr: "AXIS123456"

    },

    gateway: {

        status: "captured",

        amount: 12500,

        timestamp: "2026-09-04T10:31:00"

    },

    bank: {

        status: "pending",

        amount: 12500,

        utr: "AXIS123456",

        timestamp: null

    },

    ledger: {

        status: "pending",

        amount: 12500,

        timestamp: null

    },

    determination: {

        status: "PENDING",

        root_cause: "BANK_POSTING_DELAY",

        severity: "MEDIUM"

    },

    confidence: 94,

    timeline: [

        {
            event: "Payment captured",
            source: "gateway",
            timestamp: "2026-09-04T10:31:00",
            status: "completed"
        },

        {
            event: "Settlement processed",
            source: "gateway",
            timestamp: "2026-09-04T10:31:10",
            status: "completed"
        },

        {
            event: "Bank transfer initiated",
            source: "bank",
            timestamp: "2026-09-04T10:31:11",
            status: "completed"
        },

        {
            event: "Bank credit",
            source: "bank",
            timestamp: null,
            status: "pending"
        }

    ],

    evidence: [

        "Gateway transaction was captured",

        "Settlement was processed",

        "UTR matched across settlement and bank records",

        "Settlement amount matches bank amount"

    ],

    exceptions: [

        "Bank credit timestamp is unavailable"

    ],

    recommended_action:
        "Monitor the bank settlement using UTR AXIS123456."

};
/* =========================================================
   RENDER INVESTIGATION RESULT
========================================================= */

function loadMockInvestigation() {

    const result = mockInvestigationResult;


    /* ---------------------------------------------
       BASIC TRANSACTION DATA
    --------------------------------------------- */

    setText(
        "investigationTransactionId",
        result.transaction_id
    );

    setText(
        "investigationSettlementId",
        result.settlement.settlement_id
    );

    setText(
        "investigationAmount",
        formatCurrency(result.amount)
    );

    setText(
        "investigationCurrency",
        result.currency
    );


    /* ---------------------------------------------
       DETERMINATION
    --------------------------------------------- */

    setText(
        "investigationStatus",
        result.determination.status
    );

    setText(
        "rootCause",
        formatRootCause(result.determination.root_cause)
    );

    setText(
        "severityText",
        `${result.determination.severity} severity`
    );


    /* ---------------------------------------------
       CONFIDENCE
    --------------------------------------------- */

    setText(
        "confidenceScore",
        result.confidence
    );


    /* ---------------------------------------------
       SOURCE STATUS
    --------------------------------------------- */

    setText(
        "gatewayStatus",
        formatStatus(result.gateway.status)
    );

    setText(
        "gatewayAmount",
        formatCurrency(result.gateway.amount)
    );

    setText(
        "gatewayTimestamp",
        formatTime(result.gateway.timestamp)
    );


    setText(
        "bankStatus",
        formatStatus(result.bank.status)
    );

    setText(
        "bankUtr",
        result.bank.utr || "Unavailable"
    );


    setText(
        "ledgerStatus",
        formatStatus(result.ledger.status)
    );

    setText(
        "ledgerAmount",
        formatCurrency(result.ledger.amount)
    );


    /* ---------------------------------------------
       TIMELINE
    --------------------------------------------- */

    renderTimeline(result.timeline);


    /* ---------------------------------------------
       EVIDENCE
    --------------------------------------------- */

    renderEvidence(result.evidence);


    /* ---------------------------------------------
       EXCEPTIONS
    --------------------------------------------- */

    renderExceptions(result.exceptions);


    /* ---------------------------------------------
       RECOMMENDED ACTION
    --------------------------------------------- */

    setText(
        "recommendedAction",
        result.recommended_action
    );

}


/* =========================================================
   TIMELINE RENDERER
========================================================= */

function renderTimeline(events) {

    const container =
        document.getElementById("investigationTimeline");


    if (!container) {
        return;
    }


    container.innerHTML = "";


    events.forEach((event) => {

        const item =
            document.createElement("div");


        item.className =
            `timeline-item ${event.status === "pending" ? "pending" : ""}`;


        const timestamp =
            event.timestamp
                ? formatDateTime(event.timestamp)
                : "Timestamp unavailable";


        item.innerHTML = `

            <span class="timeline-marker"></span>

            <div class="timeline-content">

                <strong>
                    ${escapeHtml(event.event)}
                </strong>

                <span>
                    ${escapeHtml(timestamp)}
                </span>

            </div>

            <span class="timeline-source">
                ${escapeHtml(event.source)}
            </span>

        `;


        container.appendChild(item);

    });

}


/* =========================================================
   EVIDENCE RENDERER
========================================================= */

function renderEvidence(evidence) {

    const container =
        document.getElementById("evidenceList");


    if (!container) {
        return;
    }


    container.innerHTML = "";


    evidence.forEach((item) => {

        const row =
            document.createElement("div");


        row.className =
            "evidence-item";


        row.innerHTML = `

            <i data-lucide="check-circle-2"></i>

            <span>
                ${escapeHtml(item)}
            </span>

        `;


        container.appendChild(row);

    });


    initializeIcons();

}


/* =========================================================
   EXCEPTION RENDERER
========================================================= */

function renderExceptions(exceptions) {

    const container =
        document.getElementById("exceptionList");


    const count =
        document.getElementById("exceptionCount");


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (count) {
        count.textContent = exceptions.length;
    }


    exceptions.forEach((item) => {

        const row =
            document.createElement("div");


        row.className =
            "exception-item";


        row.innerHTML = `

            <i data-lucide="triangle-alert"></i>

            <span>
                ${escapeHtml(item)}
            </span>

        `;


        container.appendChild(row);

    });


    initializeIcons();

}


/* =========================================================
   HELPERS
========================================================= */

function setText(id, value) {

    const element =
        document.getElementById(id);


    if (element) {
        element.textContent = value;
    }

}


function formatCurrency(amount) {

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 0
        }
    ).format(amount);

}


function formatStatus(status) {

    if (!status) {
        return "Unavailable";
    }

    return status
        .charAt(0)
        .toUpperCase() +
        status.slice(1);

}


function formatRootCause(rootCause) {

    return rootCause
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/\b\w/g, (char) =>
            char.toUpperCase()
        );

}


function formatTime(timestamp) {

    if (!timestamp) {
        return "Unavailable";
    }


    return new Date(timestamp)
        .toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            }
        );

}


function formatDateTime(timestamp) {

    if (!timestamp) {
        return "Timestamp unavailable";
    }


    return new Date(timestamp)
        .toLocaleString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            }
        );

}


function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent = value;

    return div.innerHTML;

}