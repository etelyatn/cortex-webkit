// frontend/src/components/commands/ParamForm.tsx

import type { CapabilityParam } from "../../types/commands";

interface ParamFormProps {
  params: CapabilityParam[];
  values: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}

export function ParamForm({ params, values, onChange }: ParamFormProps) {
  return (
    <div className="border border-border rounded p-3 space-y-3 bg-bg-tertiary">
      <div className="text-xs font-semibold uppercase tracking-wider text-text-secondary">Parameters</div>
      {params.map((param) => (
        <ParamField key={param.name} param={param} value={values[param.name]} onChange={onChange} />
      ))}
    </div>
  );
}

function ParamField({
  param,
  value,
  onChange,
}: {
  param: CapabilityParam;
  value: unknown;
  onChange: (key: string, value: unknown) => void;
}) {
  const id = `param-${param.name}`;

  return (
    <div className="space-y-1">
      <label htmlFor={id} className="text-xs text-text-secondary flex items-center gap-1">
        {param.name}
        {param.required && <span className="text-error">*</span>}
      </label>
      {param.description && (
        <div className="text-xs text-text-secondary/70">{param.description}</div>
      )}

      {param.type === "boolean" ? (
        <input
          id={id}
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(param.name, e.target.checked)}
          className="accent-accent"
        />
      ) : param.type === "integer" || param.type === "number" ? (
        <input
          id={id}
          type="number"
          value={value != null ? String(value) : ""}
          placeholder={param.default != null ? String(param.default) : undefined}
          onChange={(e) => onChange(param.name, param.type === "integer" ? parseInt(e.target.value) : parseFloat(e.target.value))}
          className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-xs font-mono
                     focus:outline-none focus:border-accent"
        />
      ) : param.enum ? (
        <select
          id={id}
          value={String(value ?? "")}
          onChange={(e) => onChange(param.name, e.target.value)}
          className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-xs font-mono
                     focus:outline-none focus:border-accent"
        >
          <option value="">Select...</option>
          {param.enum.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          type="text"
          value={String(value ?? "")}
          placeholder={param.default != null ? String(param.default) : undefined}
          onChange={(e) => onChange(param.name, e.target.value)}
          className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-xs font-mono
                     focus:outline-none focus:border-accent"
        />
      )}
    </div>
  );
}
