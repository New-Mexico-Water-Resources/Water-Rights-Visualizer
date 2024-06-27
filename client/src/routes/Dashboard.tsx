import { Alert, Snackbar } from "@mui/material";
import { useEffect } from "react";
import { MapContainer, ScaleControl, TileLayer, ZoomControl } from "react-leaflet";
import useStore from "../utils/store";

import GeoJSONLayer from "../components/GeoJsonLayer";
import "../scss/Dashboard.scss";
import NavToolbar from "../components/NavToolbar";
import UploadDialog from "../components/UploadDialog";
import CurrentJobChip from "../components/CurrentJobChip";
import JobQueue from "../components/JobQueue";
import MultiGeoJSONLayer from "../components/MultiGeoJsonLayer";
import LayersControl from "../components/LayersControl";

const Dashboard = () => {
  const loadedGeoJSON = useStore((state) => state.loadedGeoJSON);
  const multipolygons = useStore((state) => state.multipolygons);
  const locations = useStore((state) => state.locations);
  const previewMode = useStore((state) => state.previewMode);
  const showUploadDialog = useStore((state) => state.showUploadDialog);
  const [successMessage, setSuccessMessage] = useStore((state) => [state.successMessage, state.setSuccessMessage]);
  const [errorMessage, setErrorMessage] = useStore((state) => [state.errorMessage, state.setErrorMessage]);

  const [isQueueOpen, setIsQueueOpen] = useStore((state) => [state.isQueueOpen, state.setIsQueueOpen]);
  const [isBacklogOpen, setIsBacklogOpen] = useStore((state) => [state.isBacklogOpen, state.setIsBacklogOpen]);

  const [pollCount, increasePollCount] = useStore((state) => [state.pollCount, state.increasePollCount]);
  const fetchQueue = useStore((state) => state.fetchQueue);

  const handleKeyPress = (event: any) => {
    const isMac = navigator.userAgent.includes("Mac");
    const isCmdOrCtrl = isMac ? event.metaKey : event.ctrlKey;

    if (isCmdOrCtrl && event.key === "b") {
      event.preventDefault();
      if (!isQueueOpen && isBacklogOpen) {
        setIsBacklogOpen(false);
      }
      setIsQueueOpen(!isQueueOpen);
    }
  };

  useEffect(() => {
    window.addEventListener("keydown", handleKeyPress);

    return () => {
      window.removeEventListener("keydown", handleKeyPress);
    };
  }, [isQueueOpen]);

  useEffect(() => {
    fetchQueue();
  }, [pollCount]);

  useEffect(() => {
    const interval = setInterval(() => {
      increasePollCount();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", overflow: "hidden" }}>
      <NavToolbar />
      {showUploadDialog && <UploadDialog />}
      {multipolygons.length <= 1 && <CurrentJobChip />}
      {multipolygons.length > 1 && previewMode && <LayersControl />}
      <JobQueue />
      <MapContainer
        className="map-container"
        center={[34.5199, -105.8701]}
        zoom={7}
        zoomControl={false}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='Imagery <a href="https://www.google.com/">Google</a>'
          url="http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
          maxZoom={20}
          subdomains={["mt0", "mt1", "mt2", "mt3"]}
        />
        <ZoomControl position="topright" />
        <ScaleControl position="bottomleft" />
        <GeoJSONLayer data={loadedGeoJSON} />
        <MultiGeoJSONLayer data={multipolygons} locations={locations} />
      </MapContainer>
      <Snackbar
        open={successMessage.length > 0}
        autoHideDuration={5000}
        onClose={() => setSuccessMessage("")}
        message={successMessage}
      >
        <Alert onClose={() => setSuccessMessage("")} severity="success" variant="filled" sx={{ width: "100%" }}>
          {successMessage}
        </Alert>
      </Snackbar>
      <Snackbar open={errorMessage.length > 0} autoHideDuration={5000} onClose={() => setErrorMessage("")}>
        <Alert onClose={() => setErrorMessage("")} severity="error" variant="filled" sx={{ width: "100%" }}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default Dashboard;
