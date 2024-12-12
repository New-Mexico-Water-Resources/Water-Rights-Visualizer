import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import Leaflet from "leaflet";
import useStore from "../utils/store";
import { area as turfArea } from "@turf/turf";

const GeoJSONLayer = ({ data, fitToBounds = true }: { data: any; fitToBounds?: boolean }) => {
  const map = useMap();
  const layerRef = useRef<any>(null);

  const minimumValidArea = useStore((state) => state.minimumValidArea);

  useEffect(() => {
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    if (data && Object.keys(data).length > 0) {
      let area = turfArea(data);
      let isValidArea = area >= minimumValidArea;
      const geoJsonLayer = new Leaflet.GeoJSON(data);

      if (!isValidArea) {
        geoJsonLayer.setStyle({
          color: "red",
          fillColor: "red",
          fillOpacity: 0.5,
        });
      }

      geoJsonLayer.addTo(map);
      if (fitToBounds) {
        map.fitBounds(geoJsonLayer.getBounds());
      }
      layerRef.current = geoJsonLayer;
    }

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [data, map, minimumValidArea]);

  return null;
};

export default GeoJSONLayer;
