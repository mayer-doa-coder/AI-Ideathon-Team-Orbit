/**
 * Boots the Agriva template's assets/js/main.js against React-rendered markup.
 *
 * main.js is an IIFE wrapped in `$(document).ready(...)`. In the original
 * static template it is the last <script> on the page, so the DOM it queries
 * already exists. Under React nothing exists at parse time, so index.html
 * loads only the vendor plugins (jQuery, GSAP, Swiper, WOW, ...) and leaves
 * main.js to us — we inject it from an effect, once the section markup has
 * actually painted. Because the document is long past `ready` by then, jQuery
 * fires the handler synchronously on injection, which is exactly what we want.
 *
 * Two consequences of injecting late are worth knowing about:
 *
 *   1. main.js's `window.load` handler — the only thing that hides
 *      #agri-preloader — will usually never fire, because load has already
 *      happened. The preloader therefore manages its own dismissal in React
 *      (see components/template/Preloader.jsx) rather than trusting main.js.
 *
 *   2. Its three `DOMContentLoaded` blocks (about-page history scrubber,
 *      image-trail, drag gallery) never run. None of them are used by
 *      index.html's sections, so the home page is unaffected. Anything that
 *      later ports about-2.html's history section needs to re-run that block
 *      by hand.
 */

// main.js binds most of its behaviour directly to elements ($(".x").on(...)),
// which dies with the DOM on unmount and is re-bound cleanly on the next
// injection. Only these three are delegated on `document`, so they SURVIVE
// React tearing the markup down and would stack up a duplicate handler on
// every re-injection. `.mean-expand` is the one that actually breaks: its
// handler toggles fa-plus/fa-minus, so a second copy toggles it straight back
// and the mobile submenu icon stops responding. They are detached before each
// boot and re-bound by main.js itself.
const DELEGATED = [
  ["click", ".mean-expand"],
  ["mouseenter", ".box-2"],
  ["click", "#back-top"],
];

const SCRIPT_MARKER = "data-agriva-main";

// True between appending the <script> and it finishing execution. Guards the
// StrictMode remount: in development React deliberately runs every effect
// mount → cleanup → mount, so without this the effect appends main.js twice
// and both copies execute, giving meanmenu two stacked mobile navs and Swiper
// two competing instances per slider.
let inFlight = false;

// Set once main.js has executed. Read by onAgrivaBooted() so a component that
// mounts after the boot still gets its callback.
let booted = false;
const bootListeners = new Set();

/**
 * Runs `callback` once the template has finished booting, and again after
 * every subsequent boot. Returns an unsubscribe function.
 *
 * Any component adding its own GSAP ScrollTriggers must go through this rather
 * than creating them in a plain effect. Two reasons:
 *   - teardown() below kills every ScrollTrigger on the page, and child effects
 *     run before the parent's boot effect — so triggers created directly would
 *     be created and then immediately destroyed.
 *   - main.js creates the ScrollSmoother, which changes how scroll positions
 *     are measured. Triggers registered before it exists end up misplaced.
 */
export function onAgrivaBooted(callback) {
  bootListeners.add(callback);
  if (booted) callback();
  return () => bootListeners.delete(callback);
}

function teardown() {
  const $ = window.jQuery;

  booted = false;

  if (window.ScrollSmoother?.get) {
    window.ScrollSmoother.get()?.kill();
  }
  if (window.ScrollTrigger?.getAll) {
    window.ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
  }

  if ($) {
    DELEGATED.forEach(([event, selector]) => $(document).off(event, selector));
    // meanmenu builds its mobile nav *outside* the React tree, inside
    // .mobile-menu. React never cleans that up, so a second boot would leave
    // two stacked mobile navs behind.
    $(".mean-bar").remove();
  }

  // An in-flight script is deliberately left in place: whether removing a
  // <script> before it executes cancels it is browser-dependent, and both
  // outcomes are worse than letting it run once against the current DOM —
  // either the page ends up with no template behaviour at all, or with the
  // duplicate execution this guard exists to prevent.
  if (!inFlight) {
    document.querySelectorAll(`script[${SCRIPT_MARKER}]`).forEach((el) => el.remove());
  }
}

/**
 * Injects main.js and returns a teardown function. Safe to call repeatedly —
 * each call fully unwinds the previous boot first. No-ops (returning a noop
 * teardown) if the vendor bundle is missing, which is what a blocked or failed
 * /assets/js/*.js request looks like; the page then renders as unenhanced but
 * fully readable static markup rather than throwing.
 */
export function bootAgrivaTemplate() {
  if (!window.jQuery || !window.gsap) {
    if (import.meta.env.DEV) {
      console.warn(
        "[agriva] jQuery/GSAP missing — template scripts did not load. " +
          "Check the vendor <script> tags in index.html."
      );
    }
    return () => {};
  }

  teardown();

  // A boot is already queued. Its script has not run yet, so it will
  // initialise against the DOM as it stands after this mount — appending a
  // second copy would only duplicate that work.
  if (inFlight) return teardown;

  inFlight = true;
  const script = document.createElement("script");
  script.src = "/assets/js/main.js";
  script.setAttribute(SCRIPT_MARKER, "");
  script.onload = () => {
    inFlight = false;
    booted = true;
    // ScrollSmoother now exists, so any trigger positions measured earlier are
    // stale. Refresh before handing control to listeners.
    window.ScrollTrigger?.refresh?.();
    bootListeners.forEach((listener) => listener());
  };
  script.onerror = () => {
    inFlight = false;
    if (import.meta.env.DEV) {
      console.warn("[agriva] /assets/js/main.js failed to load — animations are inactive.");
    }
  };
  // A freshly created <script> element re-executes even when the URL is
  // already cached, so no cache-busting query is needed to re-run main.js.
  document.body.appendChild(script);

  return teardown;
}
