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

function initializeNavigation() {

    const navItems =
        document.querySelectorAll(".nav-item");


    navItems.forEach((item) => {

        item.addEventListener("click", (event) => {

            event.preventDefault();


            navItems.forEach((navItem) => {

                navItem.classList.remove("active");

            });


            item.classList.add("active");

        });

    });

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
