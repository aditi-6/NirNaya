/* =========================================================
   SAKSHYA
   Frontend Application
========================================================= */


/* =========================================================
   ICON INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    if (window.lucide) {
        lucide.createIcons();
    }

    initializeThemeToggle();

});


/* =========================================================
   THEME TOGGLE
========================================================= */

function initializeThemeToggle() {

    const themeToggle = document.getElementById("themeToggle");

    if (!themeToggle) {
        return;
    }

    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("light-mode");

        const isLightMode =
            document.body.classList.contains("light-mode");

        localStorage.setItem(
            "NirNaya-theme",
            isLightMode ? "light" : "dark"
        );

    });

}


/* =========================================================
   RESTORE SAVED THEME
========================================================= */

const savedTheme = localStorage.getItem("NirNaya-theme");

if (savedTheme === "light") {
    document.body.classList.add("light-mode");
}
