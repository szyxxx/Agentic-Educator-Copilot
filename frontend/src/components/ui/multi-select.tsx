"use client";

import { useState } from "react";

type Props = {
  options: string[];
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
};

/** Shared comma-separated multiselect dropdown used in RPS forms. */
export function MultiSelect({ options, value, onChange, placeholder }: Props) {
  const [open, setOpen] = useState(false);
  const selected = value
    ? value.split(/[,&]+/).map((v) => v.trim()).filter(Boolean)
    : [];

  const toggleOption = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((v) => v !== opt).join(", "));
    } else {
      onChange([...selected, opt].join(", "));
    }
  };

  return (
    <div className="relative">
      <div
        className="w-full min-h-[42px] p-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white flex flex-wrap gap-1 cursor-pointer items-center"
        onClick={() => setOpen(!open)}
      >
        {selected.length === 0 && (
          <span className="text-slate-400 p-1">{placeholder}</span>
        )}
        {selected.map((s) => (
          <span
            key={s}
            className="bg-teal-100 text-teal-800 px-2 py-0.5 rounded text-xs flex items-center gap-1 shadow-sm"
          >
            {s}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                toggleOption(s);
              }}
              className="text-teal-600 hover:text-teal-900"
            >
              &times;
            </button>
          </span>
        ))}
      </div>
      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          ></div>
          <div className="absolute z-20 w-full mt-1 bg-white border border-slate-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
            {options.map((opt) => (
              <div
                key={opt}
                className="px-3 py-2 text-sm hover:bg-slate-50 cursor-pointer flex items-center gap-2 border-b border-slate-50 last:border-0"
                onClick={() => toggleOption(opt)}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(opt)}
                  readOnly
                  className="rounded text-teal-600 focus:ring-teal-500"
                />
                <span
                  className={
                    selected.includes(opt)
                      ? "font-medium text-teal-700"
                      : "text-slate-700"
                  }
                >
                  {opt}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
