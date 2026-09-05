/* =========================================================
   NIRNAYA FRONTEND
   Connected to Flask Backend API
========================================================= */

const API_BASE_URL = "";

/* =========================================================
   DOM READY
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    initializeIcons();
    initializeTheme();
    initializeNavigation();
    initializeQuickSearch();
    initializeInvestigation();
    initializeHealthDetails();
    initializeHistoryTransactions();
    initializeAlerts();
    initializeQA();
    initializeCopyActions();
    initializeNotifications();
    initializeWhatIf();

});


/* =========================================================
   LUCIDE ICONS
========================================================= */

function initializeIcons() {

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }

}


/* =========================================================
   THEME TOGGLE
========================================================= */

function initializeTheme() {

    const themeToggle =
        document.getElementById("themeToggle");

    if (!themeToggle) {
        return;
    }

    const savedTheme =
        localStorage.getItem("nirnaya-theme");

    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
    }

    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("light-mode");

        const isLight =
            document.body.classList.contains("light-mode");

        localStorage.setItem(
            "nirnaya-theme",
            isLight ? "light" : "dark"
        );

        initializeIcons();

    });

}


/* =========================================================
   NAVIGATION
========================================================= */

function initializeNavigation() {

    const navItems =
        document.querySelectorAll(".nav-item");

    const pages = {

        overview:
            document.getElementById("overviewPage"),

        investigation:
            document.getElementById("investigationPage"),

        health:
            document.getElementById("healthPage"),

        alerts:
            document.getElementById("alertsPage"),

        history:
            document.getElementById("historyPage")

    };


    function showPage(pageName) {

        Object.values(pages).forEach(page => {

            if (page) {
                page.style.display = "none";
            }

        });


        if (pages[pageName]) {
            pages[pageName].style.display = "block";
        }


        navItems.forEach(item => {

            item.classList.toggle(
                "active",
                item.dataset.page === pageName
            );

        });


        updateBreadcrumb(pageName);

        initializeIcons();

    }


    function updateBreadcrumb(pageName) {

        const breadcrumbTitle =
            document.querySelector(".breadcrumb strong");

        const titles = {

            overview: "Overview",

            investigation: "Investigate",

            health: "Settlement Health",

            alerts: "Alerts",

            history: "History"

        };


        if (breadcrumbTitle) {

            breadcrumbTitle.textContent =
                titles[pageName] || "Overview";

        }

    }


    navItems.forEach(item => {

        item.addEventListener("click", function(event) {

            event.preventDefault();

            const pageName =
                this.dataset.page;

            showPage(pageName);

        });

    });


    const backToOverview =
        document.getElementById("backToOverview");


    if (backToOverview) {

        backToOverview.addEventListener("click", () => {

            showPage("overview");

        });

    }


    /*
       Overview page's Investigate button.
       We support multiple possible IDs so the frontend
       does not break if the button ID differs slightly.
    */

    const overviewInvestigateButtons =
        document.querySelectorAll(
            "#overviewInvestigateButton, .overview-investigate-button"
        );


    overviewInvestigateButtons.forEach(button => {

        button.addEventListener("click", () => {

            showPage("investigation");

        });

    });


    /*
       Expose navigation globally so other functions
       can switch pages when required.
    */

    window.showNirnayaPage = showPage;


    showPage("overview");

}


/* =========================================================
   QUICK SEARCH BUTTONS
========================================================= */

function initializeQuickSearch() {

    const input =
        document.getElementById("investigationInput");

    const quickButtons =
        document.querySelectorAll(".quick-searches button");


    if (!input) {
        return;
    }


    quickButtons.forEach(button => {

        button.addEventListener("click", () => {

            input.value =
                button.textContent.trim();

            input.focus();

        });

    });

}


/* =========================================================
   INVESTIGATION INITIALIZATION
========================================================= */

function initializeInvestigation() {

    /*
       Overview search input
    */

    const overviewInput =
        document.getElementById("investigationInput");


    const overviewButton =
        document.getElementById("investigateButton");


    if (overviewButton) {

        overviewButton.addEventListener("click", () => {

            const transactionId =
                overviewInput?.value.trim();


            if (!transactionId) {

                showFrontendMessage(
                    "Please enter a Transaction ID.",
                    "error"
                );

                return;

            }


            openInvestigation(transactionId);

        });

    }


    /*
       Press Enter inside Overview search
    */

    if (overviewInput) {

        overviewInput.addEventListener("keydown", event => {

            if (event.key === "Enter") {

                event.preventDefault();

                const transactionId =
                    overviewInput.value.trim();


                if (!transactionId) {

                    showFrontendMessage(
                        "Please enter a Transaction ID.",
                        "error"
                    );

                    return;

                }


                openInvestigation(transactionId);

            }

        });

    }


    /*
       Investigation page search
    */

    const investigationInput =
        document.getElementById(
            "investigationTransactionInput"
        );


    const investigationButton =
        document.getElementById(
            "investigationSearchButton"
        );


    if (investigationButton) {

        investigationButton.addEventListener(
            "click",
            () => {

                const transactionId =
                    investigationInput?.value.trim();


                if (!transactionId) {

                    showFrontendMessage(
                        "Please enter a Transaction ID.",
                        "error"
                    );

                    return;

                }


                loadInvestigation(transactionId);

            }
        );

    }


    /*
       Enter key on investigation input
    */

    if (investigationInput) {

        investigationInput.addEventListener(
            "keydown",
            event => {

                if (event.key === "Enter") {

                    event.preventDefault();

                    const transactionId =
                        investigationInput.value.trim();


                    if (!transactionId) {

                        showFrontendMessage(
                            "Please enter a Transaction ID.",
                            "error"
                        );

                        return;

                    }


                    loadInvestigation(transactionId);

                }

            }
        );

    }

}


/* =========================================================
   OPEN INVESTIGATION PAGE
========================================================= */

function openInvestigation(transactionId) {

    if (typeof window.showNirnayaPage === "function") {

        window.showNirnayaPage("investigation");

    }


    /*
       Put transaction ID into investigation input
    */

    const investigationInput =
        document.getElementById(
            "investigationTransactionInput"
        );


    if (investigationInput) {

        investigationInput.value =
            transactionId;

    }


    loadInvestigation(transactionId);

}


/* =========================================================
   LOAD INVESTIGATION FROM BACKEND
========================================================= */

async function loadInvestigation(transactionId) {

    if (!transactionId) {

        showFrontendMessage(
            "Transaction ID is required.",
            "error"
        );

        return;

    }


    setInvestigationLoading(true);


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/investigate`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        transaction_id:
                            transactionId
                    })
                }
            );


        const result =
            await response.json();


        /*
           Backend can return a valid investigation
           with TRANSACTION_NOT_FOUND.
        */

        if (!response.ok) {

            throw new Error(
                result.error ||
                `Backend error: ${response.status}`
            );

        }


        window.currentInvestigation =
            result;


        renderInvestigation(result);


        /*
           Keep current transaction ID available
           for Q&A.
        */

        window.currentTransactionId =
            result.transaction_id ||
            transactionId;


        showFrontendMessage(
            "Investigation loaded successfully.",
            "success"
        );


    } catch (error) {

        console.error(
            "Investigation loading failed:",
            error
        );


        showFrontendMessage(
            error.message ||
            "Unable to load investigation.",
            "error"
        );


    } finally {

        setInvestigationLoading(false);

    }

}


/* =========================================================
   RENDER INVESTIGATION
========================================================= */

function renderInvestigation(result) {

    if (!result) {
        return;
    }


    /*
       Basic transaction information
    */

    setText(
        "investigationTransactionId",
        result.transaction_id || "Unavailable"
    );


    setText(
        "investigationSettlementId",
        result.settlement?.settlement_id ||
        "Unavailable"
    );


    setText(
        "investigationAmount",
        result.amount != null
            ? formatCurrency(result.amount)
            : "Unavailable"
    );


    setText(
        "investigationCurrency",
        result.currency || "INR"
    );


    /*
       Determination
    */

    const determination =
        result.determination || {};


    setText(
        "investigationStatus",
        formatStatus(
            determination.status
        )
    );


    setText(
        "rootCause",
        formatStatus(
            determination.root_cause
        )
    );


    setText(
        "severityText",
        formatStatus(
            determination.severity
        )
    );


    /*
       Confidence
    */

    setText(
        "confidenceScore",
        result.confidence != null
            ? `${result.confidence}%`
            : "Unavailable"
    );


    /*
       Gateway
    */

    setText(
        "gatewayStatus",
        formatStatus(
            result.gateway?.status
        )
    );


    setText(
        "gatewayAmount",
        result.gateway?.amount != null
            ? formatCurrency(
                result.gateway.amount
            )
            : "Unavailable"
    );


    setText(
        "gatewayTimestamp",
        formatDateTime(
            result.gateway?.timestamp
        )
    );


    /*
       Bank
    */

    setText(
        "bankStatus",
        formatStatus(
            result.bank?.status
        )
    );


    setText(
        "bankUtr",
        result.bank?.utr ||
        "Unavailable"
    );


    /*
       Ledger
    */

    setText(
        "ledgerStatus",
        formatStatus(
            result.ledger?.status
        )
    );


    setText(
        "ledgerAmount",
        result.ledger?.amount != null
            ? formatCurrency(
                result.ledger.amount
            )
            : "Unavailable"
    );


    /*
       Evidence
    */

    renderEvidence(
        result.evidence || []
    );


    /*
       Exceptions
    */

    renderExceptions(
        result.exceptions || []
    );


    /*
       Exception count
    */

    setText(
        "exceptionCount",
        String(
            (result.exceptions || []).length
        )
    );


    /*
       AI Explanation
    */

    const ai =
        result.ai || {};


    setText(
        "aiExplanation",
        ai.explanation ||
        ai.summary ||
        "AI explanation is unavailable."
    );


    /*
       Recommended Action
    */

    setText(
        "recommendedAction",
        result.recommended_action ||
        "No action available."
    );


    /*
       Customer Reply
    */

    setText(
        "customerReply",
        ai.customer_reply ||
        "Customer reply is unavailable."
    );


    /*
       Timeline
       
       Backend currently does not provide timeline data,
       so we explicitly show that instead of inventing events.
    */

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


    /*
       What-if is currently not implemented
    */

    initializeWhatIf();


    initializeIcons();

}


/* =========================================================
   EVIDENCE RENDERING
========================================================= */

function renderEvidence(evidence) {

    const container =
        document.getElementById(
            "evidenceList"
        );


    if (!container) {
        return;
    }


    if (!Array.isArray(evidence) ||
        evidence.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No evidence available.
            </div>
        `;

        return;

    }


    container.innerHTML =
        evidence
            .map((item, index) => {

                return `
                    <div class="evidence-item">
                        <div class="evidence-number">
                            ${index + 1}
                        </div>

                        <div class="evidence-text">
                            ${escapeHtml(item)}
                        </div>
                    </div>
                `;

            })
            .join("");


    initializeIcons();

}


/* =========================================================
   EXCEPTION RENDERING
========================================================= */

function renderExceptions(exceptions) {

    const container =
        document.getElementById(
            "exceptionList"
        );


    if (!container) {
        return;
    }


    if (!Array.isArray(exceptions) ||
        exceptions.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No exceptions detected.
            </div>
        `;

        return;

    }


    container.innerHTML =
        exceptions
            .map(item => {

                return `
                    <div class="exception-item">
                        <i data-lucide="triangle-alert"></i>

                        <span>
                            ${escapeHtml(item)}
                        </span>
                    </div>
                `;

            })
            .join("");


    initializeIcons();

}


/* =========================================================
   Q&A
========================================================= */

function initializeQA() {

    const askButton =
        document.getElementById(
            "askQuestionButton"
        );


    const questionInput =
        document.getElementById(
            "questionInput"
        );


    if (!askButton || !questionInput) {
        return;
    }


    askButton.addEventListener(
        "click",
        askQuestion
    );


    questionInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                askQuestion();

            }

        }
    );

}


/* =========================================================
   ASK QUESTION API
========================================================= */

async function askQuestion() {

    const questionInput =
        document.getElementById(
            "questionInput"
        );


    if (!questionInput) {
        return;
    }


    const question =
        questionInput.value.trim();


    if (!question) {

        showFrontendMessage(
            "Please enter a question.",
            "error"
        );

        return;

    }


    const transactionId =
        window.currentTransactionId ||
        document.getElementById(
            "investigationTransactionInput"
        )?.value.trim();


    if (!transactionId) {

        showFrontendMessage(
            "Please investigate a transaction first.",
            "error"
        );

        return;

    }


    const askButton =
        document.getElementById(
            "askQuestionButton"
        );


    if (askButton) {

        askButton.disabled = true;

        askButton.dataset.originalText =
            askButton.textContent;

        askButton.textContent =
            "Thinking...";

    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/ask`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        transaction_id:
                            transactionId,

                        question:
                            question

                    })

                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                `Backend error: ${response.status}`
            );

        }


        const answer =
            result.follow_up_answer ||
            result.answer ||
            result.explanation ||
            "No answer available.";


        /*
           If there is a dedicated Q&A answer element,
           use it.
        */

        const answerContainer =
            document.getElementById(
                "qaAnswer"
            );


        if (answerContainer) {

            answerContainer.textContent =
                answer;

        } else {

            /*
               Fallback: show the answer using a message.
            */

            showFrontendMessage(
                answer,
                "success"
            );

        }


        questionInput.value = "";


    } catch (error) {

        console.error(
            "Question request failed:",
            error
        );


        showFrontendMessage(
            error.message ||
            "Unable to answer the question.",
            "error"
        );


    } finally {

        if (askButton) {

            askButton.disabled = false;

            askButton.textContent =
                askButton.dataset.originalText ||
                "Ask";

        }

    }

}


/* =========================================================
   COPY ACTIONS
========================================================= */

function initializeCopyActions() {

    document.addEventListener(
        "click",
        async event => {

            const copyButton =
                event.target.closest(
                    "[data-copy-target]"
                );


            if (!copyButton) {
                return;
            }


            const targetId =
                copyButton.dataset.copyTarget;


            const target =
                document.getElementById(
                    targetId
                );


            if (!target) {
                return;
            }


            const text =
                target.textContent.trim();


            if (!text) {
                return;
            }


            try {

                await navigator.clipboard.writeText(
                    text
                );


                const originalHTML =
                    copyButton.innerHTML;


                copyButton.innerHTML =
                    `<i data-lucide="check"></i> Copied`;


                initializeIcons();


                setTimeout(() => {

                    copyButton.innerHTML =
                        originalHTML;

                    initializeIcons();

                }, 1500);


            } catch (error) {

                console.error(
                    "Copy failed:",
                    error
                );

                showFrontendMessage(
                    "Unable to copy.",
                    "error"
                );

            }

        }
    );

}


/* =========================================================
   NOTIFICATIONS
========================================================= */

function initializeNotifications() {

    const notificationButton =
        document.querySelector(
            "[data-notifications]"
        );


    if (!notificationButton) {
        return;
    }


    notificationButton.addEventListener(
        "click",
        () => {

            showFrontendMessage(
                "No new notifications.",
                "success"
            );

        }
    );

}


/* =========================================================
   WHAT-IF
========================================================= */

function initializeWhatIf() {

    const whatIfButtons =
        document.querySelectorAll(
            ".primary-button"
        );


    whatIfButtons.forEach(button => {

        const text =
            button.textContent
                .trim()
                .toLowerCase();


        if (text.includes("what-if") ||
            text.includes("what if")) {

            /*
               What-If backend functionality does not
               currently exist.
            */

            button.disabled = true;

            button.title =
                "What-If analysis is coming soon.";

            /*
               Avoid attaching multiple listeners.
            */

            if (
                button.dataset.whatIfInitialized !==
                "true"
            ) {

                button.addEventListener(
                    "click",
                    event => {

                        event.preventDefault();

                        showFrontendMessage(
                            "What-If analysis is coming soon.",
                            "success"
                        );

                    }
                );

                button.dataset.whatIfInitialized =
                    "true";

            }

        }

    });

}


/* =========================================================
   LOADING STATE
========================================================= */

function setInvestigationLoading(isLoading) {

    const button =
        document.getElementById(
            "investigationSearchButton"
        );


    if (!button) {
        return;
    }


    if (isLoading) {

        button.disabled = true;

        button.dataset.originalText =
            button.innerHTML;

        button.innerHTML =
            `<i data-lucide="loader-circle"></i> Loading...`;

    } else {

        button.disabled = false;

        button.innerHTML =
            button.dataset.originalText ||
            `<i data-lucide="search"></i> Investigate`;

    }


    initializeIcons();

}


/* =========================================================
   FRONTEND MESSAGE
========================================================= */

function showFrontendMessage(
    message,
    type = "success"
) {

    /*
       Remove previous message
    */

    const oldMessage =
        document.querySelector(
            ".frontend-message"
        );


    if (oldMessage) {
        oldMessage.remove();
    }


    const messageElement =
        document.createElement("div");


    messageElement.className =
        `frontend-message ${type}`;


    messageElement.textContent =
        message;


    document.body.appendChild(
        messageElement
    );


    setTimeout(() => {

        messageElement.classList.add(
            "fade-out"
        );


        setTimeout(() => {

            messageElement.remove();

        }, 300);


    }, 3000);

}


/* =========================================================
   HELPER — SET TEXT
========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    element.textContent =
        value != null
            ? value
            : "Unavailable";

}


/* =========================================================
   HELPER — FORMAT STATUS
========================================================= */

function formatStatus(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "Unavailable";

    }


    return String(value)
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );

}


/* =========================================================
   HELPER — FORMAT CURRENCY
========================================================= */

function formatCurrency(
    amount,
    currency = "INR"
) {

    if (
        amount === null ||
        amount === undefined ||
        amount === ""
    ) {

        return "Unavailable";

    }


    try {

        return new Intl.NumberFormat(
            "en-IN",
            {
                style: "currency",
                currency: currency
            }
        ).format(amount);

    } catch (error) {

        return `${currency} ${amount}`;

    }

}


/* =========================================================
   HELPER — FORMAT DATE/TIME
========================================================= */

function formatDateTime(
    timestamp
) {

    if (!timestamp) {
        return "Unavailable";
    }


    const date =
        new Date(timestamp);


    if (Number.isNaN(date.getTime())) {

        return timestamp;

    }


    return date.toLocaleString(
        "en-IN",
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

}


/* =========================================================
   HELPER — ESCAPE HTML
========================================================= */

function escapeHtml(value) {

    const div =
        document.createElement("div");


    div.textContent =
        value == null
            ? ""
            : String(value);


    return div.innerHTML;

}
function initializeHealthDetails() {
    const button = document.getElementById("viewHealthDetails");

    if (!button) return;

    button.addEventListener("click", () => {
        if (typeof window.showNirnayaPage === "function") {
            window.showNirnayaPage("health");
        }
    });
}
function initializeHistoryTransactions() {
    const rows = document.querySelectorAll(".history-transaction");

    rows.forEach(row => {
        row.addEventListener("click", () => {
            const transactionId = row.dataset.transactionId;

            if (transactionId && typeof window.openInvestigation === "function") {
                window.openInvestigation(transactionId);
            }
        });
    });
}
function initializeAlerts() {
    const button = document.getElementById("viewAlerts");

    if (!button) return;

    button.addEventListener("click", () => {
        if (typeof window.showNirnayaPage === "function") {
            window.showNirnayaPage("alerts");
        }
    });
}