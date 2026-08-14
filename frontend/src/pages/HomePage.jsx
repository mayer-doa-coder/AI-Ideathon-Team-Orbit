import MarketingLayout from "../components/marketing/MarketingLayout";
import Hero from "../components/home/Hero";
import Features from "../components/home/Features";
import About from "../components/home/About";
import ProcessSection from "../components/home/ProcessSection";
import WhyChooseUs from "../components/home/WhyChooseUs";
import Services from "../components/home/Services";
import Faq from "../components/home/Faq";
import Projects from "../components/home/Projects";
import Testimonials from "../components/home/Testimonials";
import NewsBlog from "../components/home/NewsBlog";
import BrandStrip from "../components/home/BrandStrip";

/**
 * Agriva's index.html, assembled from React components in the template's own
 * section order, with our "How it works" process section inserted after About
 * — the point where a visitor has been told what the product is and next wants
 * to know how it actually works. The page chrome, ScrollSmoother wrapper and
 * template boot all live in MarketingLayout.
 */
export default function HomePage() {
  return (
    <MarketingLayout>
      <Hero />
      <Features />
      <About />
      <ProcessSection />
      <WhyChooseUs />
      <Services />
      <Faq />
      <Projects />
      <Testimonials />
      <NewsBlog />
      <BrandStrip />
    </MarketingLayout>
  );
}
