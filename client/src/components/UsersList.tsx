import { FC, useEffect, useState } from "react";
import { Button, Divider, Typography } from "@mui/material";

import useStore, { UserListingDetails } from "../utils/store";
import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";

import "../scss/UsersList.scss";
import UserItem from "./UserItem";

const UsersList: FC = () => {
  const isUsersPanelOpen = useStore((state) => state.isUsersPanelOpen);
  const users = useStore((state) => state.users);
  const totalUsers = useStore((state) => state.totalUsers);
  const adminFetchUsers = useStore((state) => state.adminFetchUsers);
  const [currentPage, setCurrentPage] = useState(0);

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

  return (
    <div className={`users-container ${isUsersPanelOpen ? "open" : "closed"}`}>
      <Typography
        variant="h5"
        style={{ color: "var(--st-gray-30)", padding: "8px 16px", paddingBottom: 0, display: "flex", alignItems: "center" }}
      >
        Users ({totalUsers})
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "4px" }}>
          <Button
            variant="contained"
            color="secondary"
            size="small"
            onClick={() => {
              let newPage = Math.max(currentPage - 1, 0);
              if (newPage === currentPage) {
                return;
              }
              setCurrentPage(newPage);
              adminFetchUsers(newPage);
            }}
          >
            <KeyboardArrowLeftIcon />
          </Button>
          <Button
            variant="contained"
            color="secondary"
            size="small"
            onClick={() => {
              let newPage = Math.min(currentPage + 1, Math.floor(totalUsers / 25));
              if (newPage === currentPage) {
                return;
              }
              setCurrentPage(newPage);
              adminFetchUsers(newPage);
            }}
          >
            <KeyboardArrowRightIcon />
          </Button>
        </div>
      </Typography>
      <div>
        <Typography
          variant="body2"
          style={{
            color: "var(--st-gray-30)",
            padding: 0,
            display: "flex",
            alignItems: "center",
            marginLeft: "16px",
            fontSize: "12px",
            marginBottom: "4px",
          }}
        >
          Page {currentPage + 1} of {Math.floor(totalUsers / 25) + 1}
        </Typography>
      </div>
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
