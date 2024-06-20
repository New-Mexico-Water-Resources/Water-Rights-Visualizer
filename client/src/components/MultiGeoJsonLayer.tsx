import { useEffect, useState } from "react";
import { useMap } from "react-leaflet";
import Leaflet from "leaflet";
import useStore from "../utils/store";

const MultiGeoJSONLayer = ({ data }: { data: any[] }) => {
  const map = useMap();
  const [destructors, setDestructors] = useState<Function[]>([]);

  const loadedGeoJSON = useStore((state) => state.loadedGeoJSON);

  useEffect(() => {
    destructors.forEach((destructor) => {
      destructor();
    });

    setDestructors([]);

    if (data && data.length > 0 && !loadedGeoJSON) {
      let bounds: Leaflet.LatLngBounds | null = null;
      let destructors: Function[] = [];

      data.forEach((layer) => {
        const geoJsonLayer = new Leaflet.GeoJSON(layer);
        geoJsonLayer.addTo(map);
        if (!bounds) {
          bounds = geoJsonLayer.getBounds();
        } else {
          bounds.extend(geoJsonLayer.getBounds());
        }

        destructors.push(() => geoJsonLayer.remove());
        console.log(geoJsonLayer);
      });

      setDestructors(destructors);

      if (bounds) {
        map.fitBounds(bounds);
      }
    }
  }, [data, map, loadedGeoJSON]);

  return null;
};

export default MultiGeoJSONLayer;
