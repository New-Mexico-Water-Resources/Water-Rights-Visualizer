import { FC, useEffect, useState } from "react";
import { useMap } from "react-leaflet";
import Leaflet from "leaflet";
import useStore from "../utils/store";

const MultiGeoJSONLayer: FC<{ data: any[]; locations: any[] }> = ({ data, locations }) => {
  const map = useMap();
  const [destructors, setDestructors] = useState<Function[]>([]);

  const loadedGeoJSON = useStore((state) => state.loadedGeoJSON);
  const setLocations = useStore((state) => state.setLocations);

  const [selectedMapLayer, setSelectedMapLayer] = useState<number | null>(null);

  // Listen to delete keypress
  useEffect(() => {
    const handleKeyPress = (event: any) => {
      if (["Delete", "Backspace"].includes(event.key) && selectedMapLayer !== null) {
        locations[selectedMapLayer].visible = false;
        setLocations([...locations]);
        setSelectedMapLayer(null);
      }
    };

    window.addEventListener("keydown", handleKeyPress);

    return () => {
      window.removeEventListener("keydown", handleKeyPress);
    };
  }, [selectedMapLayer, locations]);

  useEffect(() => {
    destructors.forEach((destructor) => {
      destructor();
    });

    setDestructors([]);

    if (data && data.length > 0 && data.length === locations.length && !loadedGeoJSON) {
      let bounds: Leaflet.LatLngBounds | null = null;
      let destructors: Function[] = [];

      locations.forEach((location) => {
        if (!data[location.id] || !location.visible) {
          return;
        }

        const layer = data[location.id];
        const geoJsonLayer = new Leaflet.GeoJSON(layer);
        geoJsonLayer.on({
          dblclick: (evt: any) => {
            setSelectedMapLayer(location.id);
            map.fitBounds(geoJsonLayer.getBounds());
          },
          click: (evt: any) => {
            setSelectedMapLayer(location.id);
          },
        });

        let roundedAcres = Math.round(location.acres * 100) / 100;
        let roundedLat = Math.round(location.lat * 1000000) / 1000000;
        let roundedLong = Math.round(location.long * 1000000) / 1000000;

        geoJsonLayer.bindTooltip(
          `<div style='padding:1px 3px 1px 3px;display:flex;flex-direction:column;'>
            <b>${location.county} ${location.id + 1}</b>
            <b>Acres: ${roundedAcres}</b>
            <b>Coordinates: ${roundedLat}, ${roundedLong}</b>
            <b>Comments: ${location.comments || "None"}</b>
          </div>`,
          {
            direction: "right",
            permanent: false,
            sticky: true,
            offset: [10, 0],
            opacity: 0.75,
            className: "custom-tooltip",
          }
        );
        geoJsonLayer.addTo(map);

        if (!bounds) {
          bounds = geoJsonLayer.getBounds();
        } else {
          bounds.extend(geoJsonLayer.getBounds());
        }

        destructors.push(() => geoJsonLayer.remove());
      });

      setDestructors(destructors);

      if (bounds) {
        map.fitBounds(bounds);
      }
    }

    return () => {
      destructors.forEach((destructor) => {
        destructor();
      });
    };
  }, [data, map, loadedGeoJSON, locations]);

  return null;
};

export default MultiGeoJSONLayer;
