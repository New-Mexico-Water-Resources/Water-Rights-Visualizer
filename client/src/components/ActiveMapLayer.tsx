import { useEffect, useMemo } from "react";
import { TileLayer, useMap } from "react-leaflet";
import { MAP_LAYER_OPTIONS } from "../utils/constants";
import useStore, { MapLayer } from "../utils/store";

const ActiveMapLayer = () => {
  const map = useMap();

  const mapLayerKey = useStore((state) => state.mapLayerKey);
  const tileDate = useStore((state) => state.tileDate);

  const activeMapLayer = useMemo(() => {
    let mapLayer = (MAP_LAYER_OPTIONS as any)?.[mapLayerKey] as MapLayer;
    if (!mapLayer) {
      mapLayer = MAP_LAYER_OPTIONS["Google Satellite"];
    }

    let layer = JSON.parse(JSON.stringify(mapLayer));
    if (tileDate) {
      layer.url = layer.url.replace("{time}", tileDate);
    } else if (layer.time) {
      layer.url = layer.url.replace("{time}", layer.time);
    }

    return layer;
  }, [mapLayerKey, tileDate]);

  useEffect(() => {
    if (activeMapLayer.maxZoom) {
      map.setMaxZoom(activeMapLayer.maxZoom);
    }

    let currentZoom = map.getZoom();
    if (currentZoom > activeMapLayer.maxZoom) {
      map.setZoom(activeMapLayer.maxZoom);
    }
  }, [activeMapLayer, map]);

  return (
    <TileLayer
      key={activeMapLayer.name}
      url={activeMapLayer.url}
      attribution={activeMapLayer.attribution}
      maxNativeZoom={activeMapLayer.maxZoom}
      maxZoom={activeMapLayer.maxZoom}
      subdomains={activeMapLayer.subdomains || []}
      bounds={activeMapLayer?.bounds}
    />
  );
};

export default ActiveMapLayer;
