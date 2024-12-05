import { FC, useEffect } from "react";
import NavToolbar from "../components/NavToolbar";
import { Button } from "@mui/material";
import { MapContainer, TileLayer } from "react-leaflet";
import useStore from "../utils/store";

const NotFoundPage: FC = () => {
  const loadVersion = useStore((state) => state.loadVersion);

  useEffect(() => {
    loadVersion();
  }, [loadVersion]);

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", overflow: "hidden" }}>
      <NavToolbar publicMode={true} />
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          zIndex: 1000,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
            zIndex: 1000,
            padding: "16px",
            borderRadius: "16px",
            width: "600px",
            height: "300px",
            backgroundColor: "rgba(0, 0, 0, 0.75)",
          }}
        >
          <h1 style={{ fontSize: "64px", marginBottom: 0 }}>404</h1>
          <p>You seem to have gone off the map!</p>
          <Button
            variant="contained"
            color="secondary"
            sx={{
              "&:hover": {
                color: "var(--st-gray-30)",
              },
            }}
            href="/"
          >
            Return to your world
          </Button>
        </div>
      </div>
      <MapContainer className="map-container" center={[0, 0]} zoom={2} zoomControl={false} scrollWheelZoom={false}>
        <TileLayer
          attribution='Imagery <a href="https://www.google.com/">Google</a>'
          url="http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
          maxZoom={20}
          subdomains={["mt0", "mt1", "mt2", "mt3"]}
        />
      </MapContainer>
    </div>
  );
};

export default NotFoundPage;
