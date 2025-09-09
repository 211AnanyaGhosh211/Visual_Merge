import React, { useEffect, useState } from "react";
import ReactApexChart from "react-apexcharts";

const TIME_RANGES = [
  { label: "Day", value: "day" },
  { label: "Week", value: "week" },
  { label: "Month", value: "month" },
  { label: "Quarterly", value: "quarter" },
  { label: "Yearly", value: "year" },
];

// Chart options for ApexCharts
const defaultOptions = {
  colors: ["#f7eb07"],
  chart: {
    type: "bar",
    height: 320,
    fontFamily: "Inter, sans-serif",
    toolbar: { show: false },
  },
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: "40%",
      borderRadiusApplication: "end",
      borderRadius: 0,
    },
  },
  tooltip: {
    shared: true,
    intersect: false,
    style: { fontFamily: "Inter, sans-serif" },
  },
  states: {
    hover: { filter: { type: "darken", value: 1 } },
  },
  stroke: { show: true, width: 0, colors: ["transparent"] },
  grid: {
    show: true,
    borderColor: '#e5e7eb',
    strokeDashArray: 2,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
    position: 'back',
    padding: { left: 2, right: 2, top: -14 },
  },
  dataLabels: { enabled: false },
  legend: { show: false },
  xaxis: {
    floating: false,
    labels: {
      show: true,
      style: {
        fontFamily: "Inter, sans-serif",
        cssClass: "text-xs font-medium fill-gray-500 dark:fill-gray-400",
      },
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
    categories: [], // will be set dynamically
  },
  yaxis: {
    show: true,
    min: 0,
    max: 100,
    tickAmount: 10,
    labels: {
      show: true,
      style: {
        colors: ['#6b7280'],
        fontFamily: 'Inter, sans-serif',
        fontWeight: 500,
        fontSize: '12px',
      },
    },
  },
  fill: { opacity: 1 },
};

const LeadsCard = () => {
  const [series, setSeries] = useState([]);
  const [options, setOptions] = useState(defaultOptions);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [range, setRange] = useState("week");

  useEffect(() => {
    setLoading(true);
    setError(null);
    // fetch(`http://127.0.0.1:5000/api/bargraph?timerange=${range}`)
    fetch(`http://127.0.0.1:5000/api/bargraph`)

      .then((res) => res.json())
      .then((data) => {
        setSeries([
          {
            name: "Exceptions",
            data: data.exception_counts,
          },
        ]);
        setOptions((prev) => ({
          ...prev,
          xaxis: {
            ...prev.xaxis,
            categories: data.usernames,
          },
        }));
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to fetch data");
        setLoading(false);
      });
  }, [range]);

  return (
    <div className="max-w-full w-full bg-gradient-to-br from-white via-blue-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-3xl shadow-xl p-4 sm:p-6 md:p-8 lg:p-10 transition-all duration-300 hover:shadow-2xl mx-auto">
      {/* Dropdown for time range */}
      {/* <div className="flex justify-end mb-4">
        <select
          className="rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={range}
          onChange={e => setRange(e.target.value)}
        >
          {TIME_RANGES.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>  */}
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 sm:pb-6 mb-4 sm:mb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 sm:gap-4">
          <div>
            <h5 className="leading-none text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white pb-1 tracking-tight">
              Exceptions made by users
            </h5>
            <p className="text-sm sm:text-base font-medium text-gray-500 dark:text-gray-400">
              Leads generated per {range}
            </p>
          </div>
        </div>
      </div>
      {/* Bar chart section */}
      <div className="pt-2 sm:pt-4 bg-white/90 dark:bg-gray-900/80 rounded-2xl shadow-lg p-2 sm:p-4 transition-all duration-300 hover:shadow-2xl overflow-x-auto">
        <div className="min-w-[320px]">
          {loading ? (
            <div className="text-gray-500 dark:text-gray-400 text-center">
              Loading chart...
            </div>
          ) : error ? (
            <div className="text-red-500 text-center">{error}</div>
          ) : (
            (
              (["quarterly", "yearly"].includes(range) && (!series[0]?.data?.length || series[0]?.data?.every(v => v === 0)))
            ) ? (
              <div className="flex flex-col items-center justify-center h-64 text-center bg-white/70 dark:bg-gray-900/70 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 mx-auto">
                <svg className="w-12 h-12 mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v18h18M7 16l3-3 4 4 5-6" />
                </svg>
                <div className="text-lg font-semibold text-gray-400 dark:text-gray-500 mb-1">
                  No data available
                </div>
                <div className="text-sm text-gray-400 dark:text-gray-600">
                  There are no exceptions for this time range.
                </div>
              </div>
            ) : (
              <ReactApexChart options={options} series={series} type="bar" height={320} />
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default LeadsCard; 