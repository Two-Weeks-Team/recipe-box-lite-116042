export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface Recipe {
  id?: string;
  title: string;
  ingredients: string[];
  instructions: string;
  tags?: string[];
}

export async function createRecipe(recipe: Recipe) {
  const res = await fetch(`${API_BASE}/recipes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(recipe),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.message ?? "Failed to create recipe");
  }
  return res.json();
}

export async function searchRecipes(query: string) {
  const params = new URLSearchParams({ q: query });
  const res = await fetch(`${API_BASE}/recipes/search?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.message ?? "Search failed");
  }
  return res.json();
}

export async function suggestSubstitutions(ingredients: string[]) {
  const res = await fetch(`${API_BASE}/recipes/suggest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ingredients }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.message ?? "Tag suggestion failed");
  }
  return res.json();
}
