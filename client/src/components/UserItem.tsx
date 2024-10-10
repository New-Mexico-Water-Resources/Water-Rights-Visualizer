import {
  Checkbox,
  IconButton,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  SelectChangeEvent,
  Typography,
} from "@mui/material";
import { useConfirm } from "material-ui-confirm";
import { FC, useMemo, useState } from "react";
import useStore, { UserListingDetails } from "../utils/store";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import { ROLES } from "../utils/constants";

import "../scss/UserItem.scss";

const UserItem: FC<{ user: UserListingDetails }> = ({ user }) => {
  const confirm = useConfirm();
  const deleteUser = useStore((state) => state.adminDeleteUser);
  const updateUser = useStore((state) => state.adminUpdateUser);
  const loggedInUser = useStore((state) => state.userInfo);

  const roles = [
    { id: ROLES.ADMIN, name: "Admin" },
    { id: ROLES.JOB_APPROVER, name: "Job Approver" },
    { id: ROLES.NEW_MEXICO_USER, name: "New Mexico User" },
    { id: ROLES.JOB_SUBMITTER, name: "Job Submitter" },
    { id: ROLES.NEW_USER, name: "New User", default: true },
  ];

  const [userRoles, setUserRoles] = useState<string[]>(user.roles.map((role: any) => role.id));

  const isNewUser = useMemo(
    () => user.roles.length <= 1 && user.roles.find((role) => role.id === ROLES.NEW_USER),
    [user.roles]
  );

  const isLoggedInUser = useMemo(() => user.user_id === loggedInUser?.sub, [user.user_id, loggedInUser?.sub]);

  const lastLoginDate = useMemo(() => {
    return new Date(user.last_login).toLocaleString();
  }, [user.last_login]);

  const handleChange = (event: SelectChangeEvent<typeof userRoles>) => {
    const {
      target: { value },
    } = event;
    let ids = typeof value === "string" ? value.split(",") : value;

    let backendRoles = ids.filter((id) => {
      let role = roles.find((role) => role.id === id);
      return role && !role.default;
    });

    if (backendRoles.length === 0) {
      backendRoles = [roles.find((role) => role.default)?.id || ""];
    }

    updateUser(user.user_id, backendRoles);

    setUserRoles(backendRoles);
  };

  return (
    <div className="user">
      <div className="icon-container">
        <img src={user.picture} alt="user" style={{ width: "40px" }} />
        {isNewUser && !isLoggedInUser && (
          <Typography variant="body1" className="new-user-badge">
            New
          </Typography>
        )}
        {isLoggedInUser && (
          <Typography variant="body1" className="logged-in-user-badge">
            You
          </Typography>
        )}
      </div>
      <div className="user-info">
        <Typography
          className="field name"
          variant="body1"
          style={{ color: "var(--st-gray-30)", fontWeight: isLoggedInUser ? "bold" : "normal" }}
        >
          {user.name}
        </Typography>
        <Typography
          className="field email"
          variant="body2"
          style={{ color: "var(--st-gray-50)", whiteSpace: "pre", overflow: "hidden", textOverflow: "ellipsis" }}
        >
          {user.email}
        </Typography>
        <Typography
          className="field email"
          variant="body2"
          style={{ color: "var(--st-gray-50)", whiteSpace: "pre", overflow: "hidden", textOverflow: "ellipsis" }}
        >
          Active: {lastLoginDate}
        </Typography>
        <div className="roles" style={{ marginTop: "4px" }}>
          <Select
            sx={{ width: "180px" }}
            multiple
            value={userRoles}
            onChange={handleChange}
            input={<OutlinedInput className="role-selector" sx={{ padding: 0 }} />}
            renderValue={(selected) => selected.map((id) => roles.find((role) => role.id === id)?.name).join(", ")}
          >
            {roles.map((role) => (
              <MenuItem key={role.id} value={role.id}>
                <Checkbox checked={userRoles.indexOf(role.id) > -1} />
                <ListItemText primary={role.name} />
              </MenuItem>
            ))}
          </Select>
        </div>
      </div>
      <div className="actions">
        <IconButton
          onClick={() => {
            confirm({
              title: `Delete ${user.name}`,
              description: `Are you sure you want to delete ${user.name}?`,
              confirmationButtonProps: { color: "primary", variant: "contained" },
              cancellationButtonProps: { color: "secondary", variant: "contained" },
              titleProps: { sx: { backgroundColor: "var(--st-gray-90)", color: "var(--st-gray-10)" } },
              contentProps: { sx: { backgroundColor: "var(--st-gray-90)", color: "var(--st-gray-10)" } },
              dialogActionsProps: { sx: { backgroundColor: "var(--st-gray-90)" } },
            }).then(() => {
              deleteUser(user.user_id);
            });
          }}
        >
          <DeleteForeverIcon className="action" />
        </IconButton>
      </div>
    </div>
  );
};

export default UserItem;
