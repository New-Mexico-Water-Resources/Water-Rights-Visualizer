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
    formattedTimeRemaining += `${timeRemainingDays} days `;
  } else if (timeRemainingHours > 0) {
    formattedTimeRemaining += `${timeRemainingHours} hours `;
  } else if (timeRemainingMinutes > 0) {
    formattedTimeRemaining += `${timeRemainingMinutes} minutes `;
  } else if (timeRemainingSeconds > 0) {
    formattedTimeRemaining += `${timeRemainingSeconds} seconds `;
  } else {
    formattedTimeRemaining = "N/A";
  }

  return formattedTimeRemaining;
};

export default {};
