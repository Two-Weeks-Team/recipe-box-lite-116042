"use client";
import React, { useState, useEffect } from "react";
import { searchRecipes } from "./api";

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handler = setTimeout(async () => {
      if (!query) {
        setResults([]);
        return;
      }
      setLoading(true);
      try {
        const data = await searchRecipes(query);
        setResults(data.results ?? []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }, 400);
    return () => clearTimeout(handler);
  }, [query]);

  return (
    <div className="space-y-2">
      <input
        type="text"
        placeholder="Search recipes…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full border rounded p-2"
      />
      {loading && <p className="text-sm text-gray-500">Searching…</p>}
      {results.length > 0 && (
        <ul className="border rounded max-h-60 overflow-y-auto bg-white">
          {results.map((r) => (
            <li key={r.id} className="p-2 border-b last:border-b-0">
              <strong>{r.title}</strong>
              {r.match_score && (
                <span className="ml-2 text-xs text-gray-600">Score: {r.match_score.toFixed(2)}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
