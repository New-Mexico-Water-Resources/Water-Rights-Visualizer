// axiosInstance.get(`${API_URL}/admin/users`).then((response) => {
// axiosInstance.delete(`${API_URL}/admin/delete_user?userId=${userId}`).then(() => {
// .post(`${API_URL}/admin/update_user`, { userId, roles })
const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../../constants");
const { ManagementClient } = require("auth0");

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
      });

      allUsers.push(...users);

      if (users.length >= total) {
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
    const users = await fetchUsers();
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
  console.log("canUpdateUsers", canUpdateUsers, req.body, req.auth?.payload?.permissions);
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

module.exports = router;
