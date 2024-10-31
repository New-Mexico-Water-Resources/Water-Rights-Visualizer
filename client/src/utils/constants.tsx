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

export const QUEUE_STATUSES = ["Pending", "In Progress", "WaitingApproval", "Paused"];
