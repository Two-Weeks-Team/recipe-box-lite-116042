"use client";
import React, { useState } from "react";
import { createRecipe, suggestSubstitutions } from "./api";
import { TagSuggestionPopover } from "./TagSuggestionPopover";

export function RecipeForm() {
  const [title, setTitle] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [instructions, setInstructions] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [suggestedTags, setSuggestedTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleIngredientsBlur = async () => {
    const list = ingredients.split(",").map((s) => s.trim()).filter(Boolean);
    if (list.length === 0) return;
    try {
      const data = await suggestSubstitutions(list);
      setSuggestedTags(data.suggestions?.map((s: any) => s.substitute) ?? []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const recipe = {
      title,
      ingredients: ingredients.split(",").map((s) => s.trim()).filter(Boolean),
      instructions,
      tags,
    };
    try {
      await createRecipe(recipe);
      setTitle("");
      setIngredients("");
      setInstructions("");
      setTags([]);
      setSuggestedTags([]);
      alert("Recipe saved!");
    } catch (err: any) {
      alert(err.message || "Error saving recipe");
    } finally {
      setLoading(false);
    }
  };

  const addTag = (tag: string) => {
    if (!tags.includes(tag)) setTags([...tags, tag]);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded shadow">
      <div>
        <label className="block font-medium">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          className="mt-1 w-full border rounded p-2"
        />
      </div>
      <div>
        <label className="block font-medium">Ingredients (comma separated)</label>
        <input
          type="text"
          value={ingredients}
          onChange={(e) => setIngredients(e.target.value)}
          onBlur={handleIngredientsBlur}
          required
          className="mt-1 w-full border rounded p-2"
        />
        {suggestedTags.length > 0 && (
          <TagSuggestionPopover suggestions={suggestedTags} onSelect={addTag} />
        )}
      </div>
      <div>
        <label className="block font-medium">Instructions</label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          required
          className="mt-1 w-full border rounded p-2"
          rows={4}
        />
      </div>
      <div>
        <label className="block font-medium">Tags (optional, comma separated)</label>
        <input
          type="text"
          value={tags.join(", ")}
          onChange={(e) => setTags(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
          className="mt-1 w-full border rounded p-2"
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Saving..." : "Save Recipe"}
      </button>
    </form>
  );
}
