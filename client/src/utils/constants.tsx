import { CRS } from "leaflet";

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

// var USGS_USImageryTopo = L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}', {
// 	maxZoom: 20,
// 	attribution: 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
// });
// var NASAGIBS_ModisTerraChlorophyll = L.tileLayer('https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Terra_L2_Chlorophyll_A/default/{time}/{tilematrixset}{maxZoom}/{z}/{y}/{x}.{format}', {
// 	attribution: 'Imagery provided by services from the Global Imagery Browse Services (GIBS), operated by the NASA/GSFC/Earth Science Data and Information System (<a href="https://earthdata.nasa.gov">ESDIS</a>) with funding provided by NASA/HQ.',
// 	bounds: [[-85.0511287776, -179.999999975], [85.0511287776, 179.999999975]],
// 	minZoom: 1,
// 	maxZoom: 7,
// 	format: 'png',
// 	time: '',
// 	tilematrixset: 'GoogleMapsCompatible_Level',
// 	opacity: 0.75
// });

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

  // "MODIS Terra LST Day": {
  //   name: "MODIS Terra LST Day",
  //   attribution:
  //     'Imagery provided by services from the Global Imagery Browse Services (GIBS), operated by the NASA/GSFC/Earth Science Data and Information System (<a href="https://earthdata.nasa.gov">ESDIS</a>) with funding provided by NASA/HQ.',
  //   url: "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MOD16A2_ET/default/{time}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png",
  //   bounds: [
  //     [-85.0511287776, -179.999999975],
  //     [85.0511287776, 179.999999975],
  //   ],
  //   maxZoom: 9,
  //   time: "2023-01-01",
  // },
};

export const QUEUE_STATUSES = ["Pending", "In Progress", "WaitingApproval", "Paused"];
