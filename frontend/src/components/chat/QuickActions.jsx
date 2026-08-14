export default function QuickActions({ options, onSelect, disabled }) {
  return (
    <div className="quick-actions">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          className="quick-action-chip"
          onClick={() => onSelect(option)}
          disabled={disabled}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
