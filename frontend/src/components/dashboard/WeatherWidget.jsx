import { useLanguage } from "../../context/LanguageContext";

export default function WeatherWidget({ weather, live = false }) {
  const { t, tf } = useLanguage();

  if (!weather) {
    return (
      <div className="weather-widget weather-widget-pending">
        <h2>{t("weatherWidget.title")}</h2>
        <p>{t("weatherWidget.empty")}</p>
      </div>
    );
  }

  const { location, dates, daily_rainfall_mm, temp_range_c, heavy_rain_date, alert } = weather;
  const maxRain = Math.max(...daily_rainfall_mm, 1);

  return (
    <div className="weather-widget">
      <h2>
        {tf("weatherWidget.headingTemplate", { location, days: daily_rainfall_mm.length })}
        {live && (
          <span className="live-badge" title={t("weatherWidget.liveTitle")}>
            {t("weatherWidget.live")}
          </span>
        )}
      </h2>

      <div className="weather-chart">
        {daily_rainfall_mm.map((mm, i) => {
          const isHeavy = dates[i] === heavy_rain_date;
          return (
            <div
              key={i}
              className={`weather-bar ${isHeavy ? "heavy" : ""}`}
              style={{ height: `${Math.max((mm / maxRain) * 100, 8)}%` }}
              title={tf("weatherWidget.barTitleTemplate", { date: dates[i], mm })}
            />
          );
        })}
      </div>

      <div className="weather-stats">
        <span>{tf("weatherWidget.rainfallTemplate", { days: daily_rainfall_mm.length })}</span>
        <span>{tf("weatherWidget.tempTemplate", { range: temp_range_c })}</span>
      </div>

      {heavy_rain_date && (
        <div className="weather-alert">{alert}</div>
      )}
    </div>
  );
}
