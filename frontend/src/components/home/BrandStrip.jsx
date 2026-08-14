import { brandLogos } from "../../data/homeContent";

export default function BrandStrip() {
  const loop = [...brandLogos, ...brandLogos];

  return (
    <div className="brand-strip">
      <div className="brand-strip-track">
        {loop.map((src, i) => (
          <img src={src} alt="" key={i} />
        ))}
      </div>
    </div>
  );
}
