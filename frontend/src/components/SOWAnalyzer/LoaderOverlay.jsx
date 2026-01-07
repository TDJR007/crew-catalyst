// File: components/SOWAnalyzer/LoaderOverlay.jsx
import React from "react";
import Lottie from "lottie-react";
import cuteLoader from "../../assets/animations/tea-animation.json";

const LoaderOverlay = ({ message = "Loading..." }) => (
  <div className="fixed inset-0 bg-white bg-opacity-80 z-50 flex flex-col items-center justify-center space-y-4">
    <Lottie animationData={cuteLoader} loop className="w-40 h-40" />
    <p className="text-lg text-gray-700 font-medium">{message}</p>
  </div>
);

export default LoaderOverlay;