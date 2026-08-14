import { useLanguage } from "../../context/LanguageContext";
import CropCard from "./CropCard";

export default function CropComparison({ crops, selectedCropId, onSelect }) {
  const { t } = useLanguage();
  if (crops.length === 0) return null;

  return (
    <div className="crop-comparison">
      <div className="crop-comparison-header">
        <h2>{t("cropComparison.title")}</h2>
        <span className="crop-comparison-subtitle">{t("cropComparison.subtitle")}</span>
      </div>

      <div className="crop-comparison-grid">
        {crops.map((crop) => (
          <CropCard
            key={crop.id}
            crop={crop}
            isSelected={selectedCropId === crop.id}
            onSelect={() => onSelect(crop)}
          />
        ))}
      </div>
    </div>
  );
}
