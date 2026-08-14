import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import SiteHeader from "../home/SiteHeader";
import SiteFooter from "../home/SiteFooter";
import Preloader from "../template/Preloader";
import { BackToTop, MouseCursor, Offcanvas, SearchPopup } from "../template/TemplateChrome";
import { bootAgrivaTemplate } from "../../utils/agrivaTemplate";

/**
 * The Agriva page shell shared by every marketing route.
 *
 * Two structural details are load-bearing rather than decorative:
 *
 *   - #smooth-wrapper / #smooth-content must wrap the scrolling content and
 *     must NOT wrap the fixed chrome above them. main.js only creates the GSAP
 *     ScrollSmoother when both ids are present, and ScrollSmoother translates
 *     #smooth-content — anything fixed placed inside it scrolls away instead of
 *     staying pinned.
 *
 *   - bootAgrivaTemplate() runs from an effect so the whole tree below has
 *     already committed to the DOM. main.js queries for this markup the moment
 *     it executes, so booting any earlier finds nothing.
 *
 * The boot is keyed on pathname: each marketing route renders different
 * sections, so the template's sliders and ScrollTriggers have to be rebuilt
 * against the new DOM when the route changes.
 */
export default function MarketingLayout({ children }) {
  const { pathname } = useLocation();

  useEffect(() => bootAgrivaTemplate(), [pathname]);

  // Client-side navigation keeps the old scroll position, which lands the
  // visitor halfway down a page they have just opened.
  useEffect(() => {
    window.scrollTo(0, 0);
    window.ScrollSmoother?.get?.()?.scrollTo(0, false);
  }, [pathname]);

  return (
    <>
      <Preloader />
      <BackToTop />
      <MouseCursor />
      <Offcanvas />
      <SiteHeader />
      <SearchPopup />

      <div id="smooth-wrapper">
        <div id="smooth-content">
          {children}
          <SiteFooter />
        </div>
      </div>
    </>
  );
}
