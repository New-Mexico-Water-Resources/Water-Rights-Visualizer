import { FC, useEffect, useState } from "react";
import { Divider, Typography } from "@mui/material";

import useStore, { UserListingDetails } from "../utils/store";

import "../scss/UsersList.scss";
import UserItem from "./UserItem";

const UsersList: FC = () => {
  const isUsersPanelOpen = useStore((state) => state.isUsersPanelOpen);
  const fetchUsers = useStore((state) => state.adminFetchUsers);
  const users = useStore((state) => state.users);

  const [orderedUsers, setOrderedUsers] = useState(users);
  // Preserve order of users if isUsersPanelOpen is true
  useEffect(() => {
    if (!isUsersPanelOpen) {
      setOrderedUsers(users);
    } else {
      // Keep the order of users the same
      setOrderedUsers((prevUsers) => {
        let foundUsers: UserListingDetails[] = [];
        let newUsers: UserListingDetails[] = [];
        prevUsers.forEach((prevUser) => {
          let matchedUser = users.find((user) => user.user_id === prevUser.user_id);
          if (matchedUser) {
            foundUsers.push(matchedUser);
          }
        });

        users.forEach((user) => {
          if (!foundUsers.find((foundUser) => foundUser.user_id === user.user_id)) {
            newUsers.push(user);
          }
        });

        return [...foundUsers, ...newUsers];
      });
    }
  }, [users, isUsersPanelOpen]);

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div className={`users-container ${isUsersPanelOpen ? "open" : "closed"}`}>
      <Typography
        variant="h5"
        style={{ color: "var(--st-gray-30)", padding: "8px 16px", display: "flex", alignItems: "center" }}
      >
        Users
      </Typography>
      <Divider />
      <div className="users-list">
        {orderedUsers.map((user) => (
          <UserItem key={user.user_id} user={user} />
        ))}
      </div>
    </div>
  );
};

export default UsersList;
