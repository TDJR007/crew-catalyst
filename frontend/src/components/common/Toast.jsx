// components/common/Toast.jsx
import React from "react";
import { CheckCircle, AlertCircle, X, Info } from "lucide-react";

const Toast = ({ 
  message, 
  type = "success", 
  isVisible = false, 
  onClose, 
  duration = 3000 
}) => {
  React.useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  if (!isVisible) return null;

  const getToastStyles = () => {
    switch (type) {
      case 'success':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-800',
          icon: <CheckCircle className="h-5 w-5 text-green-500" />
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200', 
          text: 'text-yellow-800',
          icon: <AlertCircle className="h-5 w-5 text-yellow-500" />
        };
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-800', 
          icon: <AlertCircle className="h-5 w-5 text-red-500" />
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-800',
          icon: <Info className="h-5 w-5 text-blue-500" />
        };
    }
  };

  const styles = getToastStyles();

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className={`
        ${styles.bg} ${styles.border} ${styles.text}
        border rounded-lg shadow-lg px-4 py-3 min-w-80 max-w-md
      `}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {styles.icon}
            <span className="font-medium">{message}</span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 ml-4"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Toast;