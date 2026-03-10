"use client";
import React from "react";
import { RecipeForm } from "./RecipeForm";
import { SearchBar } from "./SearchBar";

export default function HomePage() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h1 className="text-4xl font-bold text-center">Recipe Box Lite</h1>
      <SearchBar />
      <RecipeForm />
    </div>
  );
}