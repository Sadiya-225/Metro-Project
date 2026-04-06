"use client";

import React, { useEffect, useRef, useState } from "react";
import { MapPin } from "lucide-react";
import { Station, getStations } from "@/lib/api";

interface StationAutocompleteProps {
  onSelect: (station: Station) => void;
  placeholder?: string;
  label?: string;
}

const StationAutocomplete: React.FC<StationAutocompleteProps> = ({
  onSelect,
  placeholder = "Search Metro Station",
  label,
}) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Station[]>([]);
  const [allStations, setAllStations] = useState<Station[]>([]);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getStations().then(setAllStations).catch(console.error);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setResults([]);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = (value: string) => {
    setQuery(value);
    if (value.trim().length < 2) {
      setResults([]);
      return;
    }

    const normalizedQuery = value.toLowerCase();
    const filtered = allStations
      .filter((station) =>
        [station.station_name, station.line, station.zone]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery),
      )
      .sort((a, b) => b.importance_score - a.importance_score)
      .slice(0, 10);

    setResults(filtered);
  };

  const handleSelect = (station: Station) => {
    setQuery(station.station_name);
    setResults([]);
    onSelect(station);
  };

  return (
    <div className="relative w-full" ref={wrapperRef}>
      {label && (
        <label className="mb-2 block text-sm font-medium">{label}</label>
      )}
      <div className="flex w-full rounded-lg border border-gray-300 bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-500">
        <div className="flex items-center justify-center rounded-l-lg bg-blue-100 px-3">
          <MapPin className="h-5 w-5 text-blue-600" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(event) => handleSearch(event.target.value)}
          placeholder={placeholder}
          className="w-full rounded-r-lg px-4 py-3 text-md focus:outline-none"
        />
      </div>

      {results.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-gray-300 bg-white shadow-xl">
          {results.map((station) => (
            <li
              key={station.station_id}
              className="cursor-pointer border-b px-4 py-3 text-md transition-colors hover:bg-blue-50 last:border-b-0"
              onClick={() => handleSelect(station)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{station.station_name}</div>
                  <div className="text-sm text-gray-500">
                    {station.line}
                    {station.is_interchange ? " • Interchange" : ""}
                    {station.is_terminal ? " • Terminal" : ""}
                    {station.zone ? ` • ${station.zone}` : ""}
                  </div>
                </div>
                <div className="rounded bg-blue-100 px-2 py-1 text-sm">
                  Score: {station.importance_score}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default StationAutocomplete;
