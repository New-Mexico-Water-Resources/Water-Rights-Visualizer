const os = require("os");
const path = require("path");
const { MongoClient } = require("mongodb");
require("dotenv").config();

const port = 5000;
const server_directory = __dirname;
const project_directory = path.dirname(__dirname);
// const run_directory_base = '~/data/water_rights_runs';
const run_directory_base = process.env.RUN_DIRECTORY_BASE || path.join(os.homedir(), "data/water_rights_runs");
const report_queue_collection = "report_queue";

let cachedURI = null;
let cachedDB = null;

const client_id = process.env.AUTH0_CLIENT_ID;
const issuer_base_url = process.env.AUTH0_ISSUER_BASE_URL;
const auth0_domain = process.env.AUTH0_DOMAIN;
const auth0_audience = process.env.AUTH0_AUDIENCE;

const connectToDatabase = async () => {
  let user = process.env.MONGO_INITDB_ROOT_USERNAME !== undefined ? process.env.MONGO_INITDB_ROOT_USERNAME : "admin";
  let cred =
    process.env.MONGO_INITDB_ROOT_PASSWORD !== undefined ? process.env.MONGO_INITDB_ROOT_PASSWORD : "mypassword";
  let host = process.env.MONGO_HOST !== undefined ? process.env.MONGO_HOST : "water-rights-visualizer-water_mongo-1";
  let port = process.env.MONGO_PORT !== undefined ? process.env.MONGO_PORT : 27017;
  let database = process.env.MONGO_DATABASE !== undefined ? process.env.MONGO_DATABASE : "water";

  let auth = user && cred ? `${user}:${cred}@` : "";
  const uri = `mongodb://${auth}${host}:${port}`;
  if (cachedDB && cachedURI === uri) {
    return cachedDB;
  }

  console.log("Attempting to connect to MongoDB at", uri);
  const client = new MongoClient(uri, { directConnection: true });
  try {
    await client.connect();
    console.log("Connected to MongoDB at", uri);
    const db = client.db(database);
    cachedDB = db;
    cachedURI = uri;
    return db;
  } catch (err) {
    console.error("Error connecting to MongoDB:", err);
    return null;
  }
};

module.exports = {
  port,
  server_directory,
  project_directory,
  run_directory_base,
  report_queue_collection,
  connectToDatabase,
  client_id,
  issuer_base_url,
  auth0_domain,
  auth0_audience,
};
