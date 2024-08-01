import { Button, IconButton, Typography } from "@mui/material";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import ClearAllIcon from "@mui/icons-material/ClearAll";
import SelectAllIcon from "@mui/icons-material/SelectAll";
import useStore from "../utils/store";
import { FC, useMemo, useState } from "react";
import { FixedSizeList as List } from "react-window";

import "../scss/LayersControl.scss";

const LayersControl: FC = () => {
  const setActiveJob = useStore((state) => state.setActiveJob);
  const [previewMode, setPreviewMode] = useStore((state) => [state.previewMode, state.setPreviewMode]);
  const setShowUploadDialog = useStore((state) => state.setShowUploadDialog);

  const multipolygons = useStore((state) => state.multipolygons);
  const setLoadedGeoJSON = useStore((state) => state.setLoadedGeoJSON);

  const [rows, setRows] = useStore((state) => [state.locations, state.setLocations]);

  const visibleLayerCount = useMemo(() => {
    return rows.reduce((acc, row) => (row.visible ? acc + 1 : acc), 0);
  }, [rows]);

  const [activeRowId, setActiveRowId] = useState<number | null>(null);

  const LayerRow: FC<{ index: number; style: any }> = ({ index, style }) => {
    let row = rows[index];
    if (!row) {
      console.error("No row found for index", index);
      return null;
    }

    let roundedLat = row?.lat ? Math.round(row.lat * 1000) / 1000 : "NaN";
    let roundedLong = row?.long ? Math.round(row.long * 1000) / 1000 : "NaN";

    let roundedAcres = row?.acres ? Math.round(row.acres * 100) / 100 : "NaN";

    return (
      <div key={row.id} className={`layer-row ${row.id === activeRowId ? "active" : ""}`} style={style}>
        <div className="left-btns">
          <IconButton
            onClick={() => {
              row.visible = !row.visible;
              setRows([...rows]);
            }}
          >
            {row.visible && (
              <CheckBoxIcon
                sx={{
                  cursor: "pointer",
                  "&:hover": { color: "var(--st-gray-20)" },
                }}
              />
            )}
            {!row.visible && (
              <CheckBoxOutlineBlankIcon
                sx={{
                  cursor: "pointer",
                  "&:hover": { color: "var(--st-gray-20)" },
                }}
              />
            )}
          </IconButton>
        </div>
        <div
          className="details"
          onClick={() => {
            if (row.id === activeRowId) {
              setActiveRowId(null);
              setLoadedGeoJSON(null);
            } else {
              let geojson = multipolygons[row.id];
              if (geojson) {
                setLoadedGeoJSON(geojson);
                setActiveRowId(row.id);

                if (!row.visible) {
                  row.visible = true;
                  setRows([...rows]);
                }
              }
            }
          }}
        >
          <Typography
            variant="body1"
            sx={{
              color: row.id === activeRowId ? "var(--st-gray-10)" : "var(--st-gray-30)",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              cursor: "pointer",
            }}
          >
            {row.county} {row.id + 1}
          </Typography>
          <Typography
            variant="body2"
            style={{ color: row.id === activeRowId ? "var(--st-gray-20)" : "var(--st-gray-40)" }}
          >
            Coordinates: {roundedLat}, {roundedLong}
          </Typography>
          <Typography
            variant="body2"
            style={{ color: row.id === activeRowId ? "var(--st-gray-20)" : "var(--st-gray-40)" }}
          >
            Acres: {roundedAcres}
          </Typography>
        </div>
      </div>
    );
  };

  return (
    <div className="layers-control">
      {previewMode && (
        <Button
          sx={{ margin: "8px 0" }}
          variant="contained"
          onClick={() => {
            setPreviewMode(false);
            setActiveJob(null);
            setShowUploadDialog(true);
          }}
        >
          Continue Editing
        </Button>
      )}
      <div className="metaline">
        <Typography
          variant="body1"
          style={{ color: "var(--st-gray-30)", fontWeight: "bold", cursor: "pointer" }}
          onClick={() => {
            setActiveRowId(null);
            setLoadedGeoJSON(null);
          }}
        >
          {visibleLayerCount} Visible Layers
        </Typography>
        <IconButton
          sx={{ marginLeft: "auto" }}
          onClick={() => {
            rows.forEach((row) => {
              row.visible = true;
            });
            setRows([...rows]);
          }}
        >
          <SelectAllIcon
            sx={{
              cursor: "pointer",
              color: "var(--st-gray-30)",
              "&:hover": { color: "var(--st-gray-20)" },
            }}
          ></SelectAllIcon>
        </IconButton>
        <IconButton
          onClick={() => {
            rows.forEach((row) => {
              row.visible = false;
            });
            setRows([...rows]);
          }}
        >
          <ClearAllIcon
            sx={{
              cursor: "pointer",
              color: "var(--st-gray-30)",
              "&:hover": { color: "var(--st-gray-20)" },
            }}
          ></ClearAllIcon>
        </IconButton>
      </div>
      {!rows?.length && (
        <Typography
          variant="body1"
          style={{ color: "var(--st-gray-30)", fontWeight: "bold", display: "flex", alignItems: "center", gap: "4px" }}
        >
          No layers
        </Typography>
      )}
      <div className="layer-list">
        <List className="List" height={500} itemCount={rows.length} itemSize={85} width={275}>
          {LayerRow}
        </List>
      </div>
    </div>
  );
};

export default LayersControl;
