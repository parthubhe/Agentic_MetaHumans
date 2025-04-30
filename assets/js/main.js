/* main.js
 *
 * Common site functionality:
 * 1. Removes the preloader on page load.
 * 2. Toggles mobile navigation.
 * 3. Initializes AOS (Animate on Scroll).
 * 4. Adds a scroll-to-top button.
 */

document.addEventListener("DOMContentLoaded", () => {

  // 1. Remove the preloader once the window has fully loaded
  const preloader = document.getElementById("preloader");
  if (preloader) {
    window.addEventListener("load", () => {
      // Remove the preloader element from the DOM
      preloader.remove();
    });
  }

  // 2. Mobile nav toggle
  const navMenu = document.getElementById("navmenu");
  const mobileNavToggle = document.querySelector(".mobile-nav-toggle");

  if (mobileNavToggle) {
    mobileNavToggle.addEventListener("click", function () {
      // Toggle a CSS class on the nav to show/hide it
      navMenu.classList.toggle("navbar-mobile");
      // Toggle icon classes (for example, from "bi-list" to "bi-x")
      this.classList.toggle("bi-list");
      this.classList.toggle("bi-x");
    });
  }

  // If your nav items have dropdowns, you might also handle that:
  // (Uncomment if you have dropdown <li> with a .dropdown > a)
  /*
  const navDropdowns = document.querySelectorAll(".navbar-mobile .dropdown > a");
  navDropdowns.forEach((dropdown) => {
    dropdown.addEventListener("click", function (e) {
      e.preventDefault();
      this.nextElementSibling.classList.toggle("dropdown-active");
    });
  });
  */

  // 3. Initialize AOS (Animate On Scroll) library if you're using it
  if (typeof AOS !== "undefined") {
    AOS.init({
      duration: 800,     // Animation duration in ms
      easing: "ease-in-out",
      once: true,        // Whether animation should happen only once
      mirror: false,     // Whether elements animate out while scrolling past them
    });
  }

  // 4. Scroll-to-top button
  const scrollTopBtn = document.getElementById("scroll-top");
  if (scrollTopBtn) {
    scrollTopBtn.addEventListener("click", () => {
      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    });

    // Optional: Show/hide the scroll-top button based on scroll position
    window.addEventListener("scroll", () => {
      if (window.scrollY > 100) {
        scrollTopBtn.classList.add("active");
      } else {
        scrollTopBtn.classList.remove("active");
      }
    });
  }

});
