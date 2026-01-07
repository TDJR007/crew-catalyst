// File: components/SOWAnalyzer/SOWAnalyzer.jsx
import React, { useState } from "react";
import UploadStep from "./UploadStep";
import FormStep from "./FormStep";
import RecommendationsStep from "./RecommendationsStep";
import { formatDateForInput, cleanString, cleanManager, cleanBudgetedHours } from "./utils";
import LoaderOverlay from "./LoaderOverlay";

const SOWAnalyzer = () => {
  const [currentStep, setCurrentStep] = useState("upload");
  const [file, setFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [formData, setFormData] = useState({});
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Put token somewhere central
  const TOKEN = import.meta.env.VITE_API_TOKEN;
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  // Helper function to build API URLs
  const buildApiUrl = (endpoint) => {
    if (!API_BASE_URL || API_BASE_URL === "null" || API_BASE_URL === "undefined") {
      // If no API_BASE_URL is set, assume we're serving from the same server
      return endpoint;
    }
    // If API_BASE_URL is set, use it
    return `${API_BASE_URL}${endpoint}`;
  };

  const handleFileUpload = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
      setError("");
    } else {
      setError("Please upload a PDF file");
    }
  };

  const extractSOWData = async () => {
    if (!file) return;
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(buildApiUrl("/extract_sow"), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${TOKEN}`,
        },
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to extract SOW data");

      const data = await response.json();
      setExtractedData(data);

      setFormData({
        name: data["Project Name"] || "",
        practice: data["Practice"] || "",
        technology: Array.isArray(data["Technology"]) ? data["Technology"] : [],
        category: data["Category"] || "",
        manager: cleanManager(data["Manager"]),
        client: cleanString(data["Client"]),
        partner: data["Partner"] || "",
        billingType: data["Billing Type"] || "",
        status: data["Status"] || "",
        budgetedHours: cleanBudgetedHours(data["Budgeted Hours"]),
        startDate: formatDateForInput(data["Start date"]),
        endDate: formatDateForInput(data["End Date"]),
        keepResourcesAvailable: false,
      });

      setCurrentStep("form");
    } catch (err) {
      setError("Error extracting SOW data: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(buildApiUrl("/recommend_employees_clean"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${TOKEN}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("Failed to get recommendations");

      const data = await response.json();
      setRecommendations(data);
      setCurrentStep("recommendations");
    } catch (err) {
      setError("Error getting recommendations: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetFlow = () => {
    setCurrentStep("upload");
    setFile(null);
    setExtractedData(null);
    setFormData({});
    setRecommendations(null);
    setError("");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentStep === "upload" && (
        <UploadStep
          file={file}
          error={error}
          loading={loading}
          onFileUpload={handleFileUpload}
          onAnalyze={extractSOWData}
          setFile={setFile}
        />
      )}
      {currentStep === "form" && (
        <FormStep
          formData={formData}
          setFormData={setFormData}
          loading={loading}
          error={error}
          onSubmit={handleFormSubmit}
          onCancel={resetFlow}
        />
      )}
      {currentStep === "recommendations" && (
        <RecommendationsStep
          recommendations={recommendations}
          onReset={resetFlow}
        />
      )}
      {loading && <LoaderOverlay message={currentStep === "upload" ? "Analyzing SOW..." : "Fetching Recommendations..."} />}
    </div>
  );
};

export default SOWAnalyzer;