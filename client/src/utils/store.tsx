import { create } from "zustand";
import { devtools } from "zustand/middleware";

import axios from "axios";
import { API_URL } from "./constants";

export interface JobStatus {
  status: string;
  currentYear: number;
  totalYears: number;
  fileCount: number;
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
  deleteJob: (jobKey: string) => void;
  submitJob: () => void;
  loadJob: (job: any) => void;
  downloadJob: (jobKey: string) => void;
  startNewJob: () => void;
  closeNewJob: () => void;
  fetchJobLogs: (jobKey: string) => Promise<{ logs: string }>;
  fetchJobStatus: (jobKey: string, jobName: string) => Promise<JobStatus>;
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
          return job;
        });

        let queue = formattedQueue.filter((job: any) => ["Pending", "In Progress"].includes(job.status));
        let backlog = formattedQueue.filter((job: any) => !["Pending", "In Progress"].includes(job.status));

        set({ queue, backlog });
      });
    },
    deleteJob: async (jobKey) => {
      axios
        .delete(`${API_URL}/queue/delete_job?key=${jobKey}`)
        .then(() => {
          set((state) => {
            let job = state.queue.find((item) => item.key === jobKey);

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
    submitJob: async () => {
      let jobName = get().jobName;
      let jobKey = `${jobName}_${get().startYear}_${get().endYear}_${Date.now()}`;
      let newJob = {
        key: jobKey,
        cmd: `/opt/conda/bin/python /app/water-rights-visualizer-backend-S3.py /root/data/water_rights_runs/${jobKey}/config.json`,
        status: "Pending",
        status_msg: null,
        submitted: new Date().toISOString(),
        started: null,
        ended: null,
        invoker: "to-do",
        name: jobName,
        start_year: get().startYear,
        end_year: get().endYear,
        geo_json_file: `/root/data/water_rights_runs/${jobKey}/${jobName}.geojson`,
        loaded_geo_json: get().loadedGeoJSON,
        base_dir: `/root/data/water_rights_runs/${jobKey}`,
        png_dir: `/root/data/water_rights_runs/${jobKey}/output/figures/${jobName}`,
        csv_dir: `/root/data/water_rights_runs/${jobKey}/output/monthly_nan/${jobName}`,
        years_processed: [],
      };

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
    loadJob: (job) => {
      axios
        .get(`${API_URL}/geojson?name=${job.name}&key=${job.key}`)
        .then((response) => {
          job.loaded_geo_json = response.data;
          set({ loadedGeoJSON: response.data, showUploadDialog: false });
        })
        .catch((error) => {
          set({ loadedGeoJSON: null, errorMessage: error?.message || "Error loading job" });
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
        jobName: "",
        startYear: 1985,
        endYear: 2020,
        showUploadDialog: true,
      });
    },
    closeNewJob: () => {
      set({
        showUploadDialog: false,
        loadedFile: null,
        loadedGeoJSON: null,
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
    fetchJobStatus: (jobKey, jobName) => {
      return axios
        .get(`${API_URL}/job/status?key=${jobKey}&name=${jobName}`)
        .then((response) => {
          return response.data;
        })
        .catch((error) => {
          set({ errorMessage: error?.message || "Error fetching job status" });
          return { status: "Error", currentYear: 0, totalYears: 0, fileCount: 0 };
        });
    },
  }))
);

export default useStore;
