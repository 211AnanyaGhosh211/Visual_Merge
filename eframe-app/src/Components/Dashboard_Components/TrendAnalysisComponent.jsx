import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useTheme } from "../../contexts/ThemeContext";

// Helper to get all days in a week range
const getLast7Days = () => {
  const days = [];
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    days.push(d.toLocaleDateString('en-US', { weekday: 'long' }));
  }
  return days;
};

const TrendAnalysisComponent = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState("weekly");
  const { darkMode } = useTheme();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/logs/trend_analysis?range=${timeRange}`
        );
        if (!response.ok)
          throw new Error("Failed to fetch trend analysis data");
        const result = await response.json();
        let transformedData = result.data.map((item) => ({
          label: item.label,
          count: item.count,
        }));

        // Zero-fill for weekly range
        if (timeRange === 'weekly') {
          const allDays = getLast7Days();
          // Map by just the day name
          const dataMap = Object.fromEntries(transformedData.map(d => [d.label.split(' ')[0], d.count]));
          transformedData = allDays.map(label => ({
            label,
            count: dataMap[label] || 0
          }));
        }

        setData(transformedData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    setLoading(true);
    fetchData();
  }, [timeRange]);

  // Set colors based on mode
  const lineColor = darkMode ? '#fff' : '#000';
  const textColor = darkMode ? '#fff' : '#222';

  return (
    <div className="max-w-full w-full bg-gradient-to-br from-white via-blue-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-3xl shadow-xl p-4 sm:p-6 md:p-8 lg:p-10 transition-all duration-300 hover:shadow-2xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">Trend Analysis</h1>
        <select
          className="px-4 py-2 border rounded-md text-sm dark:bg-neutral-800 dark:text-white dark:border-neutral-700"
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
        >
          <option value="weekly">Weekly (7 days)</option>
          <option value="monthly">Monthly (weeks)</option>
          <option value="quarterly">Quarterly (months)</option>
          <option value="yearly">Yearly (12 months)</option>
        </select>
      </div>
    <div className="bg-white dark:bg-neutral-800 p-4 mt-4 rounded-3xl shadow-xl border border-gray-100 dark:border-neutral-70 h-96">

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-600 dark:text-gray-300">
          Loading trend data...
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-64 text-red-500">
          Error: {error}
        </div>
      ) : !data || data.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          No trend data available for this period.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={350}>
          <LineChart
            data={data}
            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#444' : '#ccc'} />
            <XAxis 
              dataKey="label" 
              interval={0} 
              angle={-35} 
              textAnchor="end" 
              height={60} 
              dy={10}
              stroke={textColor}
              tick={{ fill: textColor, fontSize: 10 }}
            />
            <YAxis allowDecimals={false} stroke={textColor} tick={{ fill: textColor }} />
            <Tooltip contentStyle={{ background: darkMode ? '#222' : '#fff', color: textColor, borderRadius: 8, border: '1px solid #6366F1' }}
              labelStyle={{ color: textColor }}
              itemStyle={{ color: textColor }}
            />
            <Legend wrapperStyle={{ color: textColor }} />
            <Line
              type="monotone"
              dataKey="count"
              name="Detections"
              stroke={darkMode ? '#ffffff' : '#000000'}
              strokeWidth={3}
              dot={{ r: 5, stroke: darkMode ? '#fff' : '#000000', fill: darkMode ? '#222' : '#fff' }}
              activeDot={{ r: 8, stroke: darkMode ? '#fff' : '#000000', fill: darkMode ? '#222' : '#fff' }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  </div>

  );
};

export default TrendAnalysisComponent;
