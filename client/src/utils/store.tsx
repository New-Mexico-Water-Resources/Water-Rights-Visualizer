import { create } from "zustand";
import { devtools } from "zustand/middleware";

import axios from "axios";
import { API_URL } from "./constants";
import { formatElapsedTime, formJobForQueue } from "./helpers";

export interface PolygonLocation {
  visible: boolean;
  id: number;
  acres: number;
  comments: string;
  county: string;
  polygon_So: string;
  shape_Area: number;
  shape_Leng: number;
  source: string;
  wUR_Basin: string;
  lat: number;
  long: number;
}

export interface JobStatus {
  status: string;
  currentYear: number;
  totalYears: number;
  fileCount: number;
  estimatedPercentComplete: number;
  timeRemaining: number;
}

interface Store {
  isQueueOpen: boolean;
  setIsQueueOpen: (isQueueOpen: boolean) => void;
  isBacklogOpen: boolean;
  setIsBacklogOpen: (isBacklogOpen: boolean) => void;
  jobName: string;
  setJobName: (jobName: string) => void;
  minYear: number;
  setMinYear: (minYear: number) => void;
  maxYear: number;
  setMaxYear: (maxYear: number) => void;
  startYear: number;
  setStartYear: (startYear: number) => void;
  endYear: number;
  setEndYear: (endYear: number) => void;
  loadedFile: File | null;
  setLoadedFile: (loadedFile: File | null) => void;
  loadedGeoJSON: any;
  setLoadedGeoJSON: (loadedGeoJSON: any) => void;
  multipolygons: any[];
  setMultipolygons: (multipolygons: any[]) => void;
  previewMode: boolean;
  setPreviewMode: (previewMode: boolean) => void;
  showUploadDialog: boolean;
  setShowUploadDialog: (showUploadDialog: boolean) => void;
  activeJob: any | null;
  setActiveJob: (activeJob: any | null) => void;
  successMessage: string;
  setSuccessMessage: (successMessage: string) => void;
  errorMessage: string;
  setErrorMessage: (errorMessage: string) => void;
  pollCount: number;
  increasePollCount: () => void;
  queue: any[];
  setQueue: (queue: any[]) => void;
  backlog: any[];
  setBacklog: (backlog: any[]) => void;
  fetchQueue: () => void;
  deleteJob: (jobKey: string, deleteFiles?: boolean) => void;
  bulkDeleteJobs: (jobKeys: string[], deleteFiles?: boolean) => void;
  previewJob: (job: any) => void;
  previewMultipolygonJob: () => void;
  submitJob: () => void;
  locations: PolygonLocation[];
  setLocations: (locations: PolygonLocation[]) => void;
  prepareMultipolygonJob: () => any[];
  submitMultipolygonJob: (jobs: any[]) => void;
  loadJob: (job: any) => void;
  downloadJob: (jobKey: string) => void;
  startNewJob: () => void;
  closeNewJob: () => void;
  fetchJobLogs: (jobKey: string) => Promise<{ logs: string }>;
  jobStatuses: Record<string, JobStatus>;
  fetchJobStatus: (jobKey: string, jobName: string) => Promise<JobStatus>;
  prepareGeoJSON: (shapefile: File) => Promise<any>;
  clearPendingJobs: () => void;
}

const useStore = create<Store>()(
  devtools((set, get) => ({
    isQueueOpen: false,
    setIsQueueOpen: (isQueueOpen) => set({ isQueueOpen }),
    isBacklogOpen: false,
    setIsBacklogOpen: (isBacklogOpen) => set({ isBacklogOpen }),
    jobName: "",
    setJobName: (jobName) => set({ jobName }),
    minYear: 1985,
    setMinYear: (minYear) => set({ minYear }),
    maxYear: 2020,
    setMaxYear: (maxYear) => set({ maxYear }),
    startYear: 1985,
    setStartYear: (startYear) => set({ startYear }),
    endYear: 2020,
    setEndYear: (endYear) => set({ endYear }),
    loadedFile: null,
    setLoadedFile: (loadedFile) => set({ loadedFile }),
    loadedGeoJSON: null,
    setLoadedGeoJSON: (loadedGeoJSON) => set({ loadedGeoJSON }),
    multipolygons: [],
    setMultipolygons: (multipolygons) => set({ multipolygons }),
    previewMode: false,
    setPreviewMode: (previewMode) => set({ previewMode }),
    showUploadDialog: true,
    setShowUploadDialog: (showUploadDialog) => set({ showUploadDialog }),
    activeJob: null,
    setActiveJob: (activeJob) => set({ activeJob }),
    successMessage: "",
    setSuccessMessage: (successMessage) => set({ successMessage }),
    errorMessage: "",
    setErrorMessage: (errorMessage) => set({ errorMessage }),
    pollCount: 0,
    increasePollCount: () => set((state) => ({ pollCount: state.pollCount + 1 })),
    queue: [],
    setQueue: (queue) => set({ queue }),
    backlog: [],
    setBacklog: (backlog) => set({ backlog }),
    fetchQueue: async () => {
      axios.get(`${API_URL}/queue/list`).then((response) => {
        if (!response?.data || !Array.isArray(response.data)) {
          return set({ queue: [], backlog: [] });
        }

        let formattedQueue = response.data.map((job: any) => {
          job.submitted = job.submitted ? new Date(job.submitted).toLocaleString() : null;
          job.started = job.started ? new Date(job.started).toLocaleString() : null;
          job.ended = job.ended ? new Date(job.ended).toLocaleString() : null;
          job.timeElapsed =
            job.started && job.ended
              ? formatElapsedTime(new Date(job.ended).getTime() - new Date(job.started).getTime())
              : null;
          return job;
        });

        let queue = formattedQueue.filter((job: any) => ["Pending", "In Progress"].includes(job.status));
        let backlog = formattedQueue.filter((job: any) => !["Pending", "In Progress"].includes(job.status));

        set({ queue, backlog });
      });
    },
    deleteJob: async (jobKey, deleteFiles: boolean = true) => {
      axios
        .delete(`${API_URL}/queue/delete_job?key=${jobKey}&deleteFiles=${deleteFiles ? "true" : "false"}`)
        .then(() => {
          set((state) => {
            let job = state.queue.find((item) => item.key === jobKey);
            if (!job) {
              job = state.backlog.find((item) => item.key === jobKey);
            }

            if (!job) {
              return {
                ...state,
                errorMessage: `Error deleting job: ${jobKey} not found`,
              };
            }

            return {
              ...state,
              queue: job ? state.queue.filter((item) => item.key !== jobKey) : state.queue,
              successMessage: job ? `Job "${job.name}" deleted successfully` : "",
              errorMessage: job ? "" : `Error deleting job: ${job.name} not found`,
            };
          });
        })
        .catch((error) => {
          set(() => ({ errorMessage: error?.message || "Error deleting job" }));
        });
    },
    bulkDeleteJobs: async (jobKeys, deleteFiles: boolean = true) => {
      axios
        .delete(`${API_URL}/queue/bulk_delete_jobs`, {
          data: { keys: jobKeys, deleteFiles },
        })
        .then(() => {
          set((state) => {
            let deletedJobs = state.queue.filter((item) => jobKeys.includes(item.key));
            let remainingJobs = state.queue.filter((item) => !jobKeys.includes(item.key));

            return {
              ...state,
              queue: remainingJobs,
              successMessage: `${deletedJobs.length} jobs deleted successfully`,
              errorMessage: "",
            };
          });
        })
        .catch((error) => {
          set(() => ({ errorMessage: error?.message || "Error deleting jobs" }));
        });
    },
    previewJob: (job: any) => {
      set({ activeJob: job, showUploadDialog: false, previewMode: true });
    },
    previewMultipolygonJob: () => {
      set({ showUploadDialog: false, previewMode: true, activeJob: null });
    },
    submitJob: async () => {
      let jobName = get().jobName;
      let newJob = formJobForQueue(jobName, get().startYear, get().endYear, get().loadedGeoJSON);

      axios
        .post(`${API_URL}/start_run`, {
          name: jobName,
          startYear: get().startYear,
          endYear: get().endYear,
          geojson: get().loadedGeoJSON,
        })
        .then((response) => {
          set({
            showUploadDialog: false,
            previewMode: false,
            loadedFile: null,
            activeJob: newJob,
            successMessage: response.data,
            errorMessage: "",
          });
          get().increasePollCount();
        })
        .catch((error) => {
          set({ errorMessage: error?.message || "Error submitting job" });
        });
    },
    locations: [],
    setLocations: (locations) => set({ locations }),
    prepareMultipolygonJob: () => {
      let baseName = get().jobName;
      let multipolygons = get().multipolygons;
      let polygonLocations = get().locations;

      if (multipolygons.length === 0 || polygonLocations.length !== multipolygons.length) {
        set({ errorMessage: "No multipolygons to submit" });
        return [];
      }

      return polygonLocations
        .filter((location) => location.visible)
        .map((location) => {
          let roundedLat = Math.round(location.lat * 1000) / 1000;
          let roundedLong = Math.round(location.long * 1000) / 1000;
          let jobName = `${baseName} Part ${location.id + 1} (${roundedLat}, ${roundedLong})`;
          let geojson = multipolygons[location.id];

          return formJobForQueue(jobName, get().startYear, get().endYear, geojson);
        });
    },
    submitMultipolygonJob: async (jobs: any[]) => {
      try {
        let responses = [];
        for (const job of jobs) {
          const response = await axios.post(`${API_URL}/start_run`, {
            name: job.name,
            startYear: job.start_year,
            endYear: job.end_year,
            geojson: job.loaded_geo_json,
          });
          responses.push(response.data);
        }

        set({
          showUploadDialog: false,
          previewMode: false,
          loadedFile: null,
          multipolygons: [],
          locations: [],
          successMessage: `All ${jobs.length} jobs submitted successfully!`,
          errorMessage: "",
          activeJob: jobs[0],
          loadedGeoJSON: jobs[0].loaded_geo_json,
        });
      } catch (error: any) {
        set({
          errorMessage: error?.message || `Error submitting multipolygon job! (${error})`,
          successMessage: "",
        });
      }
    },
    loadJob: (job) => {
      axios
        .get(`${API_URL}/geojson?name=${job.name}&key=${job.key}`)
        .then((response) => {
          let loadedGeoJSON = null;
          let multipolygons = [];
          if (response?.data?.geojsons) {
            multipolygons = response.data.geojsons;
          } else {
            loadedGeoJSON = response.data;
            job.loaded_geo_json = response.data;
          }

          set({ loadedGeoJSON, multipolygons, showUploadDialog: false, previewMode: false });
        })
        .catch((error) => {
          set({ loadedGeoJSON: null, multipolygons: [], errorMessage: error?.message || "Error loading job" });
        });
      set({ activeJob: job });
    },
    downloadJob: (jobKey) => {
      let job = get().queue.find((item) => item.key === jobKey);
      if (!job) {
        job = get().backlog.find((item) => item.key === jobKey);
      }

      if (!job) {
        set({ errorMessage: `Error downloading job: ${jobKey} not found` });
        return;
      }

      window.open(`${API_URL}/download?name=${job.name}&key=${job.key}`);
    },
    startNewJob: () => {
      set({
        loadedFile: null,
        loadedGeoJSON: null,
        multipolygons: [],
        jobName: "",
        startYear: 1985,
        endYear: 2020,
        showUploadDialog: true,
        previewMode: false,
      });
    },
    closeNewJob: () => {
      set({
        showUploadDialog: false,
        previewMode: false,
        loadedFile: null,
        loadedGeoJSON: null,
        multipolygons: [],
        jobName: "",
        startYear: 1985,
        endYear: 2020,
      });
    },
    fetchJobLogs: (jobKey) => {
      return axios
        .get(`${API_URL}/job/logs?key=${jobKey}`)
        .then((response) => {
          return response.data;
        })
        .catch((error) => {
          set({ errorMessage: error?.message || "Error fetching job logs" });
          return { logs: "" };
        });
    },
    jobStatuses: {},
    fetchJobStatus: (jobKey, jobName) => {
      return axios
        .get(`${API_URL}/job/status?key=${jobKey}&name=${jobName}`)
        .then((response) => {
          set((state) => {
            let jobStatuses = { ...state.jobStatuses };
            jobStatuses[jobKey] = response.data;
            return { jobStatuses };
          });
          return response.data;
        })
        .catch((error) => {
          set((state) => ({
            errorMessage: error?.message || "Error fetching job status",
            jobStatuses: {
              ...state.jobStatuses,
              [jobKey]: {
                status: "Error fetching job status",
                currentYear: 0,
                totalYears: 0,
                fileCount: 0,
                estimatedPercentComplete: 0,
                timeRemaining: 0,
              },
            },
          }));
          return {
            status: "Error",
            currentYear: 0,
            totalYears: 0,
            fileCount: 0,
            estimatedPercentComplete: 0,
            timeRemaining: 0,
          };
        });
    },
    prepareGeoJSON: (geoFile: File) => {
      let formData = new FormData();
      formData.append("file", geoFile);

      return axios
        .post(`${API_URL}/prepare_geojson`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        })
        .then((response) => {
          return response;
        })
        .catch((error) => {
          set({ errorMessage: error?.response?.data || error?.message || "Error preparing file" });
        });
    },
    clearPendingJobs: () => {
      let pendingJobs = get()
        .queue.filter((job) => job.status === "Pending")
        .map((job) => job.key);

      if (pendingJobs.length === 0) {
        return;
      }

      get().bulkDeleteJobs(pendingJobs, true);
    },
  }))
);

export default useStore;
