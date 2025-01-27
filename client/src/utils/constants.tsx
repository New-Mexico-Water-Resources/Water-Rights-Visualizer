export const API_URL = import.meta.env.VITE_API_URL || "/api";

export const authConfig = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN || "",
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || "",
  audience: import.meta.env.VITE_AUTH0_AUDIENCE || "",
};

export const ROLES = {
  ADMIN: import.meta.env.VITE_ADMIN_ROLE,
  NEW_MEXICO_USER: import.meta.env.VITE_NEW_MEXICO_USER_ROLE,
  NEW_USER: import.meta.env.VITE_NEW_USER_ROLE,
  JOB_APPROVER: import.meta.env.VITE_JOB_APPROVER,
  JOB_SUBMITTER: import.meta.env.VITE_JOB_SUBMITTER,
};

export const MAP_LAYER_OPTIONS = {
  "Google Satellite": {
    name: "Google Satellite",
    attribution: 'Imagery <a href="https://www.google.com/">Google</a>',
    url: "http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}&hl=en",
    maxZoom: 20,
    subdomains: ["mt0", "mt1", "mt2", "mt3"],
  },
  "Google Street View": {
    name: "Google Street View",
    attribution: 'Imagery <a href="https://www.google.com/">Google</a>',
    url: "http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&hl=en",
    maxZoom: 20,
    subdomains: ["mt0", "mt1", "mt2", "mt3"],
  },
  "ESRI World Imagery": {
    name: "ESRI World Imagery",
    attribution:
      "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    maxZoom: 18,
  },
  "ESRI NatGeo World Map": {
    name: "ESRI NatGeo World Map",
    attribution:
      "Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
    maxZoom: 16,
  },
  "USGS US Imagery": {
    name: "USGS US Imagery",
    attribution: 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>',
    url: "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}",
    maxZoom: 16,
  },
  "USGS US Imagery Topo": {
    name: "USGS US Imagery Topo",
    attribution: 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>',
    url: "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}",
    maxZoom: 16,
  },
  "MODIS Terra True Color CR": {
    name: "MODIS Terra True Color CR",
    attribution:
      'Imagery provided by services from the Global Imagery Browse Services (GIBS), operated by the NASA/GSFC/Earth Science Data and Information System (<a href="https://earthdata.nasa.gov">ESDIS</a>) with funding provided by NASA/HQ.',
    url: "https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Terra_CorrectedReflectance_TrueColor/default/{time}/GoogleMapsCompatible_Level{maxZoom}/{z}/{y}/{x}.jpg",
    maxZoom: 9,
    time: "2023-01-01",
  },
  // "MODIS ET 500": {
  //   name: "MODIS ET 500",
  //   attribution:
  //     'Imagery re-formatted and made available from the NASA MODIS MOD16A2 dataset, "Steve Running, Qiaozhen Mu - University of Montana and MODAPS SIPS - NASA. (2015). MOD16A2 MODIS/Terra Evapotranspiration 8-day L4 Global 500m SIN Grid. NASA LP DAAC. http://doi.org/10.5067/MODIS/MOD16A2.006"',
  //   url: "http://localhost:5001/tiles/ET/{time}/{z}/{x}/{y}.png",
  //   maxZoom: 9,
  //   time: "2023-01-01",
  // },
};

export const QUEUE_STATUSES = ["Pending", "In Progress", "WaitingApproval", "Paused"];
