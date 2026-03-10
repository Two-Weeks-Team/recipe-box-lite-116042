"use client";
import React from "react";

interface Props {
  suggestions: string[];
  onSelect: (tag: string) => void;
}

export function TagSuggestionPopover({ suggestions, onSelect }: Props) {
  if (suggestions.length === 0) return null;
  return (
    <div className="mt-2 p-2 bg-gray-100 rounded shadow">
      <p className="font-medium mb-1">Suggested tags:</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((tag) => (
          <button
            key={tag}
            onClick={() => onSelect(tag)}
            className="px-2 py-1 bg-indigo-200 rounded hover:bg-indigo-300"
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  );
}
