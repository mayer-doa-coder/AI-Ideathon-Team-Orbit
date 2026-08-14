import SiteHeader from "../components/home/SiteHeader";
import Hero from "../components/home/Hero";
import Features from "../components/home/Features";
import About from "../components/home/About";
import WhyChooseUs from "../components/home/WhyChooseUs";
import Services from "../components/home/Services";
import Faq from "../components/home/Faq";
import Testimonials from "../components/home/Testimonials";
import NewsBlog from "../components/home/NewsBlog";
import BrandStrip from "../components/home/BrandStrip";
import SiteFooter from "../components/home/SiteFooter";
import "../styles/home.css";

export default function HomePage() {
  return (
    <div className="home-page">
      <SiteHeader />
      <Hero />
      <Features />
      <About />
      <WhyChooseUs />
      <Services />
      <Faq />
      <Testimonials />
      <NewsBlog />
      <BrandStrip />
      <SiteFooter />
    </div>
  );
}
