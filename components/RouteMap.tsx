"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { RouteResponse, Station } from "@/lib/api";

interface RouteMapProps {
  source: Station | null;
  destination: Station | null;
  route: RouteResponse | null;
  stations: Station[];
}

const MAP_STYLE =
  "https://api.maptiler.com/maps/streets-v2/style.json?key=X8chXEtN8gGlWO2Km6HQ";

const makeMarker = (
  backgroundColor: string,
  size: number,
  borderColor = "#ffffff",
) => {
  const element = document.createElement("div");
  element.style.width = `${size}px`;
  element.style.height = `${size}px`;
  element.style.borderRadius = "9999px";
  element.style.backgroundColor = backgroundColor;
  element.style.border = `2px solid ${borderColor}`;
  element.style.boxShadow = "0 2px 6px rgba(0, 0, 0, 0.25)";
  return element;
};

const getLineColor = (line: string, isInterchange: boolean) => {
  const normalizedLine = line.toUpperCase();

  if (normalizedLine.includes("RED")) return "#ef4444";
  if (normalizedLine.includes("BLUE")) return "#3b82f6";
  if (normalizedLine.includes("GREEN")) return "#10b981";
  if (isInterchange) return "#f97316";
  return "#6366f1";
};

const isValidCoordinate = (station: Station | null | undefined) =>
  Boolean(
    station &&
    Number.isFinite(station.longitude) &&
    Number.isFinite(station.latitude),
  );

const RouteMap: React.FC<RouteMapProps> = ({
  source,
  destination,
  route,
  stations,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      center: [78.4744, 17.4065],
      zoom: 11,
    });

    // Handle missing sprite images to prevent console errors
    map.on("styleimagemissing", (e) => {
      const id = e.id;
      if (!map.hasImage(id)) {
        // Create a blank 1x1 transparent image
        const img = new Image(1, 1);
        img.src =
          "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII=";
        img.onload = () => {
          if (!map.hasImage(id)) {
            map.addImage(id, img as any);
          }
        };
      }
    });

    mapRef.current = map;

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      for (const sourceId of [
        "shortest-route",
        "actual-route",
        "transfer-route",
      ]) {
        if (map.getLayer(sourceId)) map.removeLayer(sourceId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      }
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    const syncMap = () => {
      const validStations = stations.filter(isValidCoordinate);
      const stationByName = new Map(
        validStations.map((station) => [station.station_name, station]),
      );

      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];

      for (const sourceId of [
        "shortest-route",
        "actual-route",
        "transfer-route",
      ]) {
        if (map.getLayer(sourceId)) map.removeLayer(sourceId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      }

      validStations.forEach((station) => {
        const lineColor = getLineColor(station.line, station.is_interchange);
        const popup = new maplibregl.Popup({
          offset: 16,
          className: "custom-popup",
        }).setHTML(`
          <div style="font-family: Arial, sans-serif; padding: 16px; border-radius: 12px; min-width: 200px; background: white;">
            <h3 style="font-size: 16px; font-weight: 700; color: #1f2937; margin: 0 0 8px 0;">${station.station_name}</h3>
            <p style="font-size: 15px; color: #6b7280; margin: 4px 0;">
              <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: ${lineColor}; margin-right: 6px;"></span>
              ${station.line}
            </p>
            <p style="font-size: 15px; color: #9ca3af; margin: 4px 0;">Zone: <strong style="color: #4b5563;">${station.zone}</strong></p>
            <p style="font-size: 15px; color: #9ca3af; margin: 4px 0;">Importance: <strong style="color: #4b5563;">${station.importance_score}</strong></p>
            ${station.is_interchange ? '<p style="font-size: 15px; color: #ef4444; margin: 4px 0; font-weight: 600;">Interchange Station</p>' : ""}
          </div>
        `);

        markersRef.current.push(
          new maplibregl.Marker({ element: makeMarker(lineColor, 12) })
            .setLngLat([station.longitude, station.latitude])
            .setPopup(popup)
            .addTo(map),
        );
      });

      if (isValidCoordinate(source)) {
        markersRef.current.push(
          new maplibregl.Marker({ element: makeMarker("#16a34a", 18) })
            .setLngLat([source!.longitude, source!.latitude])
            .addTo(map),
        );
      }

      if (isValidCoordinate(destination)) {
        markersRef.current.push(
          new maplibregl.Marker({ element: makeMarker("#dc2626", 18) })
            .setLngLat([destination!.longitude, destination!.latitude])
            .addTo(map),
        );
      }

      if (!route) {
        if (validStations.length > 1) {
          const bounds = new maplibregl.LngLatBounds();
          validStations.forEach((station) =>
            bounds.extend([station.longitude, station.latitude]),
          );
          map.fitBounds(bounds, { padding: 40, maxZoom: 12 });
        }
        return;
      }

      const shortestCoordinates = route.shortest_path
        .map((stationName) => stationByName.get(stationName))
        .filter((station): station is Station => isValidCoordinate(station))
        .map((station) => [station.longitude, station.latitude]);

      const actualCoordinates = route.actual_path
        .map((stationName) => stationByName.get(stationName))
        .filter((station): station is Station => isValidCoordinate(station))
        .map((station) => [station.longitude, station.latitude]);

      const transferCoordinates = route.transfer_segments
        .map((segment) => {
          const fromStation = stationByName.get(segment.from_station);
          const toStation = stationByName.get(segment.to_station);
          if (
            !isValidCoordinate(fromStation) ||
            !isValidCoordinate(toStation)
          ) {
            return null;
          }
          return [
            [fromStation!.longitude, fromStation!.latitude],
            [toStation!.longitude, toStation!.latitude],
          ];
        })
        .filter((coords): coords is number[][] => Boolean(coords));

      if (shortestCoordinates.length > 1) {
        map.addSource("shortest-route", {
          type: "geojson",
          data: {
            type: "Feature",
            properties: {},
            geometry: { type: "LineString", coordinates: shortestCoordinates },
          },
        });
        map.addLayer({
          id: "shortest-route",
          type: "line",
          source: "shortest-route",
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": "#16a34a",
            "line-width": 5,
            "line-opacity": 0.85,
          },
        });
      }

      if (actualCoordinates.length > 1) {
        map.addSource("actual-route", {
          type: "geojson",
          data: {
            type: "Feature",
            properties: {},
            geometry: { type: "LineString", coordinates: actualCoordinates },
          },
        });
        map.addLayer({
          id: "actual-route",
          type: "line",
          source: "actual-route",
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": "#ef4444",
            "line-width": 4,
            "line-opacity": 0.9,
          },
        });
      }

      if (transferCoordinates.length > 0) {
        map.addSource("transfer-route", {
          type: "geojson",
          data: {
            type: "FeatureCollection",
            features: transferCoordinates.map((coords) => ({
              type: "Feature",
              properties: {},
              geometry: { type: "LineString", coordinates: coords },
            })),
          },
        });
        map.addLayer({
          id: "transfer-route",
          type: "line",
          source: "transfer-route",
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": "#f59e0b",
            "line-width": 6,
            "line-dasharray": [1, 1],
            "line-opacity": 0.95,
          },
        });
      }

      route.station_congestion.forEach((item) => {
        const station = stationByName.get(item.station_name);
        if (!isValidCoordinate(station)) {
          return;
        }

        const congestionCircle = document.createElement("div");
        const size = Math.max(16, Math.min(36, item.congestion_score / 2));
        congestionCircle.style.width = `${size}px`;
        congestionCircle.style.height = `${size}px`;
        congestionCircle.style.borderRadius = "9999px";
        congestionCircle.style.backgroundColor = "rgba(250, 204, 21, 0.18)";
        congestionCircle.style.border = "2px solid rgba(234, 179, 8, 0.6)";

        markersRef.current.push(
          new maplibregl.Marker({ element: congestionCircle })
            .setLngLat([station!.longitude, station!.latitude])
            .addTo(map),
        );
      });

      route.bottleneck_stations.forEach((stationName) => {
        const station = stationByName.get(stationName);
        if (!isValidCoordinate(station)) {
          return;
        }

        const hotspot = document.createElement("div");
        hotspot.className = "animate-pulse";
        hotspot.style.width = "18px";
        hotspot.style.height = "18px";
        hotspot.style.borderRadius = "9999px";
        hotspot.style.backgroundColor = "#dc2626";
        hotspot.style.border = "3px solid rgba(254, 202, 202, 0.9)";

        markersRef.current.push(
          new maplibregl.Marker({ element: hotspot })
            .setLngLat([station!.longitude, station!.latitude])
            .addTo(map),
        );
      });

      const allCoordinates = [...shortestCoordinates, ...actualCoordinates];
      if (allCoordinates.length > 1) {
        const bounds = new maplibregl.LngLatBounds();
        allCoordinates.forEach((coordinate) =>
          bounds.extend(coordinate as [number, number]),
        );
        map.fitBounds(bounds, { padding: 50 });
      }
    };

    if (map.isStyleLoaded()) {
      syncMap();
      return;
    }

    map.once("load", syncMap);
    return () => {
      map.off("load", syncMap);
    };
  }, [destination, route, source, stations]);

  return (
    <div className="h-130 w-full overflow-hidden rounded-xl border-2 border-gray-200">
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
};

export default RouteMap;
