const express = require("express");
const router = express.Router();

router.get("/user_info", async (req, res) => {
  let userInfoEndpoint = req.auth?.payload?.aud?.find((aud) => aud.endsWith("/userinfo"));
  if (!userInfoEndpoint) {
    res.status(401).send("Unauthorized: missing userinfo endpoint");
    return;
  }

  try {
    let userInfo = await fetch(userInfoEndpoint, {
      headers: {
        Authorization: req.headers.authorization,
      },
    }).then((res) => res.json());

    if (!userInfo) {
      res.status(401).send("Unauthorized: missing userinfo");
      return;
    }

    userInfo.permissions = req.auth?.payload?.permissions || [];
    res.status(200).send(userInfo);
  } catch (error) {
    console.error("Error fetching userinfo:", error);
    res.status(500).send("Error fetching userinfo");
    return;
  }
});

module.exports = router;
