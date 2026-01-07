// File: components/SOWAnalyzer/RecommendationsStep.jsx
import React from "react";
import {
  User,
  CheckCircle,
  AlertCircle,
  Sparkles,
  Briefcase,
  Code,
  Users,
  ShieldCheck,
  Code2,
} from "lucide-react";

const RecommendationsStep = ({ recommendations, onReset }) => {
  const allEmployees = recommendations?.recommendations || [];
  const total = recommendations?.summary?.initial_shortlisted_candidates || {};
  const sowData = recommendations?.sow_data || {};

  // Role categorization by designation
  const groupByRole = (employees) => {
    const managers = [];
    const testers = [];
    const developers = [];

    employees.forEach((employee) => {
      const designation = employee.designation?.toLowerCase() || '';

      if (designation.includes('manager')) {
        managers.push(employee);
      } else if (designation.includes('test')) {
        testers.push(employee);
      } else {
        developers.push(employee);
      }
    });

    return { managers, testers, developers };
  };

  const { managers, testers, developers } = groupByRole(allEmployees);

  const roleSections = [
    {
      title: "Managers",
      employees: managers,
      icon: <ShieldCheck className="h-5 w-5 text-indigo-600 mr-2" />,
      borderColor: "border-indigo-500",
    },
    {
      title: "Testers",
      employees: testers,
      icon: <Users className="h-5 w-5 text-rose-600 mr-2" />,
      borderColor: "border-rose-500",
    },
    {
      title: "Developers",
      employees: developers,
      icon: <Code2 className="h-5 w-5 text-green-600 mr-2" />,
      borderColor: "border-green-500",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Employee Recommendations
        </h2>
        <p className="text-gray-600">
          Found {allEmployees.length} recommended employees from{" "}
          {total.total || 0} initially shortlisted candidates
        </p>
      </div>

      {/* SOW Info */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6 border-l-4 border-green-500">
        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <Briefcase className="h-5 w-5 text-green-600 mr-2" />
          Project Information
        </h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
              <Sparkles className="h-4 w-4 text-blue-500 mr-2" />
              Practice
            </h4>
            {sowData.practice ? (
              <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                {sowData.practice}
              </span>
            ) : (
              <span className="text-gray-500 italic">No practice specified</span>
            )}
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
              <Code className="h-4 w-4 text-purple-500 mr-2" />
              Technologies
            </h4>
            {sowData.technology && sowData.technology.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {[...new Set(sowData.technology)].map((tech, index) => (
                  <span
                    key={index}
                    className="inline-block bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-gray-500 italic">No technologies specified</span>
            )}
          </div>
        </div>
      </div>

      {/* Role-Based Sections */}
      {roleSections.map(
        ({ title, employees, icon, borderColor }, index) =>
          employees.length > 0 && (
            <div key={index} className="mb-8">
              <h3 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                {icon}
                {title} ({employees.length})
              </h3>

              <div className="grid gap-6">
                {employees.map((employee, idx) => (
                  <div
                    key={idx}
                    className={`bg-white rounded-lg shadow-lg p-6 border-l-4 ${borderColor}`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="bg-gray-100 rounded-full p-2">
                          <User className="h-6 w-6 text-gray-600" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900">
                            #{employee.rank} {employee.name}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span className="bg-gray-200 px-3 py-1.5 rounded-md text-sm font-bold text-gray-800">
                              {employee.designation}
                            </span>
                            <span>
                              Match Score:{" "}
                              {(employee.match_score * 100).toFixed(0)}%
                            </span>
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-medium ${employee.recommendation_level?.toLowerCase() ===
                                "highly recommended"
                                ? "bg-green-100 text-green-800"
                                : employee.recommendation_level === "recommended"
                                  ? "bg-blue-100 text-blue-800"
                                  : "bg-yellow-100 text-yellow-800"
                                }`}
                            >
                              {employee.recommendation_level}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6 mb-4">
                      <Strengths
                        title="Key Strengths"
                        icon={
                          <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                        }
                        items={employee.key_strengths}
                      />
                      <Strengths
                        title="Concerns"
                        icon={
                          <AlertCircle className="h-4 w-4 text-yellow-500 mr-2 mt-0.5" />
                        }
                        items={employee.concerns}
                      />
                    </div>

                    {employee.why_pick && (
                      <div className="bg-gray-50 p-4 rounded-md border border-dashed border-blue-200">
                        <p className="text-sm text-gray-700">
                          <span className="mr-1 text-blue-600">✨</span>
                          <strong className="text-blue-800">Why this pick?</strong>{" "}
                          {employee.why_pick}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
      )}

      {/* Reset Button */}
      <div className="mt-8 text-center">
        <button
          onClick={onReset}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700"
        >
          Analyze Another SOW
        </button>
      </div>
    </div>
  );
};

const Strengths = ({ title, icon, items = [] }) => (
  <div>
    <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
    <ul className="space-y-1">
      {items.map((item, idx) => (
        <li key={idx} className="text-sm text-gray-700 flex items-start">
          {icon}
          {item}
        </li>
      ))}
    </ul>
  </div>
);

export default RecommendationsStep;