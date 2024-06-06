import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import Leaflet from "leaflet";

const GeoJSONLayer = ({ data }: { data: any }) => {
  const map = useMap();
  const layerRef = useRef<any>(null);

  useEffect(() => {
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    if (data) {
      const geoJsonLayer = new Leaflet.GeoJSON(data);
      geoJsonLayer.addTo(map);
      map.fitBounds(geoJsonLayer.getBounds());
      layerRef.current = geoJsonLayer;
    }
  }, [data, map]);

  return null;
};

export default GeoJSONLayer;
