// utils.js

export const formatDateForInput = (dateString) => {
  if (!dateString) return "";

  const mmddyyyy = dateString.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (mmddyyyy) {
    const [, month, day, year] = mmddyyyy;
    return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
  }

  const yyyymmdd = dateString.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (yyyymmdd) return dateString;

  return "";
};

export const cleanString = (str) => {
  if (!str) return "";
  return str.replace(/^(Client:|Manager:|Partner:)\s*/i, "").trim();
};

export const cleanManager = (manager) => {
  if (!manager) return "";
  return manager.replace(/based on the rules given:\\s*Manager:\\s*/i, "").trim();
};

export const cleanBudgetedHours = (hours) => {
  if (!hours) return "";
  return hours.toString().replace(/\\s*Budgeted Hours\\s*/i, "").trim();
};
