export const formatElapsedTime = (elapsedTime: number): string => {
  let formattedTimeRemaining = "";

  let timeRemainingSeconds = elapsedTime / 1000;
  let timeRemainingMinutes = Math.floor(timeRemainingSeconds / 60);
  timeRemainingSeconds = Math.floor(timeRemainingSeconds % 60);
  let timeRemainingHours = Math.floor(timeRemainingMinutes / 60);
  timeRemainingMinutes = Math.floor(timeRemainingMinutes % 60);
  let timeRemainingDays = Math.floor(timeRemainingHours / 24);
  timeRemainingHours = Math.floor(timeRemainingHours % 24);

  if (timeRemainingDays > 0) {
    if (timeRemainingHours > 0) {
      timeRemainingDays += timeRemainingHours / 24;
      timeRemainingDays = Math.round(timeRemainingDays * 10) / 10;
    }

    formattedTimeRemaining += `${timeRemainingDays} days `;
  } else if (timeRemainingHours > 0) {
    if (timeRemainingMinutes > 0) {
      timeRemainingHours += timeRemainingMinutes / 60;
      timeRemainingHours = Math.round(timeRemainingHours * 10) / 10;
    }
    formattedTimeRemaining += `${timeRemainingHours} hours `;
  } else if (timeRemainingMinutes > 0) {
    if (timeRemainingSeconds > 0) {
      timeRemainingMinutes += 1;
    }
    formattedTimeRemaining += `${timeRemainingMinutes} minutes `;
  } else if (timeRemainingSeconds > 0) {
    formattedTimeRemaining += `< 1 minute `;
  } else {
    formattedTimeRemaining = "N/A";
  }

  return formattedTimeRemaining;
};

export default {};
