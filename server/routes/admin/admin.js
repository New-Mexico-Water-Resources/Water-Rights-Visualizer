// axiosInstance.get(`${API_URL}/admin/users`).then((response) => {
// axiosInstance.delete(`${API_URL}/admin/delete_user?userId=${userId}`).then(() => {
// .post(`${API_URL}/admin/update_user`, { userId, roles })
const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../../constants");
const { ManagementClient } = require("auth0");

const cachedUsers = {
  data: [],
  lastUpdated: 0,
};

const DEEP_CACHE_DURATION = 60000; // 1 minute
const SHALLOW_CACHE_DURATION = 600000; // 10 minutes

const managementClient = new ManagementClient({
  domain: constants.auth0_domain,
  clientId: constants.auth0_management_client_id,
  clientSecret: constants.auth0_management_client_secret,
  scope: "read:users write:admin",
  audience: `https://${constants.auth0_domain}/api/v2/`,
  grantType: "client_credentials",
});

async function fetchUsers() {
  try {
    const allUsers = [];
    let page = 0;
    while (true) {
      const {
        data: { users, total },
      } = await managementClient.users.getAll({
        include_totals: true,
        page: page++,
        per_page: 50,
      });

      allUsers.push(...users);

      if (allUsers.length >= total) {
        break;
      }

      if (page >= 20) {
        break;
      }
    }

    let usersWithPermissions = await allUsers.map(async (user) => {
      // Fetch user permissions
      let permissionsResponse = await managementClient.users.getPermissions({ id: user.user_id });
      user.permissions = (permissionsResponse?.data || []).map((permission) => permission.permission_name);

      let rolesResponse = await managementClient.users.getRoles({ id: user.user_id });
      user.roles = (rolesResponse?.data || []).map((role) => ({ name: role.name, id: role.id }));
      return user;
    });

    return Promise.all(usersWithPermissions);
  } catch (error) {
    console.error("Error fetching users from Auth0:", error);
    throw error;
  }
}

router.get("/users", async (req, res) => {
  let canReadUsers = req.auth?.payload?.permissions?.includes("read:users") || false;
  if (!canReadUsers) {
    res.status(401).send({ error: "Unauthorized: missing read:users permission" });
    return;
  }

  try {
    let lastUpdateTimeString = new Date(cachedUsers?.lastUpdated || 0).toLocaleString();
    // If users were fetched less than 1 minute ago, return cached users without any additional requests
    if (cachedUsers.lastUpdated > Date.now() - DEEP_CACHE_DURATION) {
      res.status(200).send(cachedUsers.data);
      console.log("Returning cached users, last updated", `\x1b[32m${lastUpdateTimeString}\x1b[0m`);
      return;
    }

    // If users were fetched less than 10 minute ago, check user count and return cached users if count is the same
    let allUsers = await managementClient.users.getAll({ include_totals: true });
    if (cachedUsers.lastUpdated > Date.now() - SHALLOW_CACHE_DURATION && cachedUsers.data.length === allUsers.data.total) {
      console.log("Returning cached users, count is the same, last updated", `\x1b[32m${lastUpdateTimeString}\x1b[0m`);
      res.status(200).send(cachedUsers.data);
      return;
    }

    const users = await fetchUsers();
    cachedUsers.data = users;
    cachedUsers.lastUpdated = Date.now();
    res.status(200).send(users);
  } catch (error) {
    console.error("Failed to fetch users from Auth0:", error);
    res.status(500).send({ error: "Failed to fetch users" });
  }
});

router.delete("/delete_user", async (req, res) => {
  let canDeleteUsers = req.auth?.payload?.permissions?.includes("write:admin") || false;
  if (!canDeleteUsers) {
    res.status(401).send("Unauthorized: missing write:admin permission");
    return;
  }

  let userId = req.query.userId;
  if (!userId) {
    res.status(400).send({ error: "Missing userId" });
    return;
  }

  try {
    await managementClient.users.delete({ id: userId });
    res.status(200).send("User deleted");
  } catch (error) {
    console.error("Failed to delete user from Auth0:", error);
    res.status(500).send({ error: "Failed to delete user" });
  }
});

router.post("/update_user", async (req, res) => {
  let canUpdateUsers = req.auth?.payload?.permissions?.includes("write:admin") || false;
  if (!canUpdateUsers) {
    res.status(401).send({ error: "Unauthorized: missing write:admin permission" });
    return;
  }

  let userId = req.body.userId;
  let roles = req.body.roles;
  if (!userId) {
    res.status(400).send({ error: "Missing userId" });
    return;
  }

  try {
    if (!roles || roles.length === 0) {
      roles = [constants.auth0_new_user_role];
    }

    // Get current user roles, assign new roles, delete old roles
    let response = await managementClient.users.getRoles({ id: userId });
    let currentRoles = response.data;
    let currentRoleIds = currentRoles.map((role) => role.id);
    let newRoleIds = roles.filter((roleId) => !currentRoleIds.includes(roleId));
    let oldRoleIds = currentRoleIds.filter((roleId) => !roles.includes(roleId));

    if (newRoleIds.length > 0) {
      await managementClient.users.assignRoles({ id: userId }, { roles: newRoleIds });
    }

    if (oldRoleIds.length > 0) {
      await managementClient.users.deleteRoles({ id: userId }, { roles: oldRoleIds });
    }

    res.status(200).send({ message: "User updated" });
  } catch (error) {
    console.error("Failed to update user from Auth0:", error);
    res.status(500).send({ error: "Failed to update user" });
  }
});

router.post("/reverify_email", async (req, res) => {
  let userId = req.body.userId;
  if (!userId) {
    res.status(400).send({ error: "Missing userId" });
    return;
  }

  if (userId !== req.auth.payload.sub) {
    res.status(401).send({ error: "Unauthorized: userId does not match authenticated user" });
    return;
  }

  try {
    await managementClient.jobs.verifyEmail({ user_id: userId });
    res.status(200).send({ message: "Verification email sent" });
  } catch (error) {
    console.error("Failed to send verification email from Auth0:", error);
    res.status(500).send({ error: "Failed to send verification email" });
  }
});

module.exports = router;
