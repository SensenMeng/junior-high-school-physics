import { useState, useCallback } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (inputValue.trim() && !loading) {
        onSearch(inputValue.trim());
      }
    },
    [inputValue, loading, onSearch]
  );

  return (
    <div className="search-bar-wrapper">
      <form className="search-bar" onSubmit={handleSubmit}>
        <input
          className="search-input"
          type="text"
          placeholder="输入物理问题，例如：什么是浮力？"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        <button className="search-btn" type="submit" disabled={loading}>
          {loading ? "搜索中..." : "搜索"}
        </button>
      </form>
    </div>
  );
}
