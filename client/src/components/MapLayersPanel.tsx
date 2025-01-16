import { FC, useMemo } from "react";
import { Checkbox, Divider, FormControlLabel, FormLabel, Radio, RadioGroup, Typography } from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";

import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";

import useStore, { MapLayer } from "../utils/store";

import "../scss/MapLayersPanel.scss";
import { MAP_LAYER_OPTIONS } from "../utils/constants";
import dayjs from "dayjs";

const MapLayersPanel: FC = () => {
  const isMapLayersPanelOpen = useStore((state) => state.isMapLayersPanelOpen);

  const showARDTiles = useStore((state) => state.showARDTiles);
  const toggleARDTiles = useStore((state) => state.toggleARDTiles);

  const mapLayerOptions = useMemo(() => Object.values(MAP_LAYER_OPTIONS) as MapLayer[], [MAP_LAYER_OPTIONS]);
  const mapLayerKey = useStore((state) => state.mapLayerKey);
  const setMapLayerKey = useStore((state) => state.setMapLayerKey);

  const tileDate = useStore((state) => state.tileDate);
  const setTileDate = useStore((state) => state.setTileDate);

  const today = useMemo(() => dayjs().format("YYYY-MM-DD"), []);

  return (
    <div className={`map-layers-container ${isMapLayersPanelOpen ? "open" : "closed"}`}>
      <Typography
        variant="h5"
        style={{ color: "var(--st-gray-30)", padding: "8px 16px", display: "flex", alignItems: "center" }}
      >
        Layers
      </Typography>
      <Divider />
      <Typography
        variant="body2"
        style={{ color: "var(--st-gray-30)", padding: "8px 16px", display: "flex", alignItems: "center" }}
      >
        Active layers and reference objects showing on the map
      </Typography>
      <div className="map-layers-list">
        <Typography
          variant="h6"
          sx={{
            color: "var(--st-gray-20)",
            padding: 0,
            margin: 0,
            marginTop: "8px",
            display: "flex",
            alignItems: "center",
            borderBottom: "1px solid var(--st-gray-70)",
          }}
        >
          References
        </Typography>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "8px 16px",
            paddingTop: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", marginRight: "auto" }}>
            <Checkbox
              onClick={() => toggleARDTiles()}
              checked={showARDTiles}
              style={{ padding: 0, marginRight: "4px", marginLeft: "4px" }}
            />
            <Typography variant="body2" style={{ color: "var(--st-gray-30)", fontSize: "12px" }}>
              Available Data Boundary
            </Typography>
          </div>
        </div>
        <Typography
          variant="h6"
          sx={{
            color: "var(--st-gray-20)",
            padding: 0,
            margin: 0,
            marginTop: "8px",
            display: "flex",
            alignItems: "center",
            borderBottom: "1px solid var(--st-gray-70)",
          }}
        >
          Base Map
        </Typography>
        <div style={{ display: "flex", alignItems: "center", marginRight: "auto" }}>
          <RadioGroup
            style={{ padding: 0, marginRight: "4px", marginLeft: "16px" }}
            value={mapLayerKey}
            onChange={(evt) => {
              if (evt.target.value && mapLayerOptions.find((option) => option.name === evt.target.value)) {
                let selectedLayer = mapLayerOptions.find((option) => option.name === evt.target.value) as MapLayer;
                setMapLayerKey(selectedLayer.name);
              }
            }}
          >
            {mapLayerOptions.map((option) => {
              return (
                <>
                  <FormControlLabel key={option.name} value={option.name} control={<Radio />} label={option.name} />
                  {option?.time && mapLayerKey === option.name && (
                    <div style={{ display: "flex", alignItems: "center", marginRight: "auto" }}>
                      <LocalizationProvider dateAdapter={AdapterDayjs}>
                        <div>
                          <FormLabel style={{ color: "var(--st-gray-30)", fontSize: "12px", marginBottom: 0, padding: 0 }}>
                            Target Date
                          </FormLabel>
                          <DatePicker
                            sx={{ marginTop: "0", padding: 0 }}
                            className="date-picker"
                            defaultValue={dayjs(today)}
                            value={dayjs(tileDate)}
                            onAccept={(selectedDate) => {
                              setTileDate(selectedDate?.format("YYYY-MM-DD") || today);
                            }}
                          />
                        </div>
                      </LocalizationProvider>
                    </div>
                  )}
                </>
              );
            })}
          </RadioGroup>
        </div>
      </div>
    </div>
  );
};

export default MapLayersPanel;
