// File: components/SOWAnalyzer/UploadStep.jsx
import React from "react";
import { Upload, X, CheckCircle, AlertCircle } from "lucide-react";

const UploadStep = ({ file, error, loading, onFileUpload, onAnalyze, setFile }) => {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">SOW Extraction</h1>
        <p className="text-gray-600">
          Upload your Statement of Work PDF to get employee recommendations
        </p>
      </div>

      <label
        htmlFor="file-upload"
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer block"
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <div className="space-y-2">
          <span className="text-lg font-medium text-gray-900">
            Upload SOW PDF
          </span>
          <p className="text-gray-500">or drag and drop your PDF file here</p>
        </div>
        <input
          id="file-upload"
          type="file"
          accept=".pdf"
          onChange={onFileUpload}
          className="hidden"
        />
      </label>

      {file && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="text-green-800">{file.name}</span>
          </div>
          <button
            onClick={() => setFile(null)}
            className="text-red-600 hover:text-red-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      <div className="mt-6 text-center">
        <button
          onClick={onAnalyze}
          disabled={!file || loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Analyzing..." : "Analyze SOW"}
        </button>
      </div>
    </div>
  );
};

export default UploadStep;
