import React, { useState, useEffect } from "react";
import { ResponsivePie } from '@nivo/pie';

// Custom hook to reactively detect Tailwind's dark mode
function useIsDark() {
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains('dark')
  );
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);
  return isDark;
}

// Professional, muted color palette
const proColors = [
  "#6366F1", // Indigo
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#F43F5E", // Rose
  "#06B6D4", // Cyan
  "#A78BFA", // Soft Purple
  "#FBBF24", // Soft Yellow
  "#60A5FA", // Blue
  "#34D399", // Green
  "#F87171", // Red
];

const generateColors = (length) => {
  const result = [];
  for (let i = 0; i < length; i++) {
    result.push(proColors[i % proColors.length]);
  }
  return result;
};

const PieChartComponent = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const isDark = useIsDark();
  const [chartKey, setChartKey] = useState(isDark ? 'dark' : 'light');

  useEffect(() => {
    setChartKey(isDark ? 'dark' : 'light');
  }, [isDark]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/exception_piechart`
        );
        if (!response.ok)
          throw new Error("Failed to fetch dashboard statistics");
        const result = await response.json();
        const colors = generateColors(result.length);
        const transformedData = result.map((item, idx) => ({
          id: item.label,
          label: item.label,
          value: item.value,
          color: colors[idx],
        }));
        setData(transformedData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    setLoading(true);
    fetchData();
  }, []);

  const total = data.reduce((sum, item) => sum + item.value, 0);

  // Elegant center label
  const CenteredMetric = ({ centerX, centerY, isDark }) => (
    <g>
      <text
        x={centerX}
        y={centerY - 10}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={16}
        fontWeight={500}
        fill={isDark ? "#fff" : "#6B7280"}
        style={{ letterSpacing: 1 }}
        key="total-label"
      >
        Total
      </text>
      <text
        x={centerX}
        y={centerY + 18}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={20}
        fontWeight={700}
        fill={isDark ? "#fff" : "#111"}
        style={{ letterSpacing: 1 }}
        key="total-value"
      >
        {total}
      </text>
    </g>
  );

  if (loading) {
    return (
      <div className="w-full h-72 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-72 flex items-center justify-center">
        <p className="text-red-500 dark:text-red-400">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl w-full bg-gradient-to-br from-gray-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-3xl shadow-2xl p-6 md:p-10 transition-all duration-300 hover:shadow-2xl ml-0">
      <h3 className="leading-none text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white  pb-1 tracking-tight">
        Exception Distribution
      </h3>
      <div className="bg-white dark:bg-neutral-800 p-4 mt-4 rounded-3xl shadow-xl border border-gray-100 dark:border-neutral-700 items-center justify-center relative h-64 sm:h-80 md:h-96">
        <ResponsivePie
          key={chartKey}
          data={data}
          margin={{ top: 40, right: 40, bottom: 40, left: 40 }}
          innerRadius={0.8}
          padAngle={2}
          cornerRadius={1}
          activeOuterRadiusOffset={10}
          colors={{ datum: 'data.color' }}
          borderWidth={2}
          borderColor={{ from: 'color', modifiers: [['darker', 0.18]] }}
          enableArcLinkLabels={true}
          arcLinkLabelsTextColor={isDark ? "#fff" : "#111"}
          arcLinkLabelsThickness={2}
          arcLinkLabelsColor={{ from: 'color' }}
          arcLinkLabelsDiagonalLength={18}
          arcLinkLabelsStraightLength={24}
          arcLabelsTextColor={isDark ? "#fff" : "#111"}
          arcLabelsSkipAngle={10}
          arcLabel={d => `${Math.round((d.value / total) * 100)}%`}
          tooltip={({ datum }) => (
            <div style={{ padding: 14, background: isDark ? '#222' : '#fff', border: '1.5px solid #6366F1', borderRadius: 12, boxShadow: '0 4px 24px rgba(79,70,229,0.10)', color: isDark ? '#fff' : '#222', fontWeight: 500, fontFamily: 'Inter, sans-serif', minWidth: 90 }}>
              <span style={{ color: datum.color, fontWeight: 700 }}>{datum.label}</span>: {datum.value}
            </div>
          )}
          legends={[
            {
              anchor: 'bottom',
              direction: 'row',
              justify: false,
              translateX: 0,
              translateY: 56,
              itemsSpacing: 0,
              itemWidth: 100,
              itemHeight: 18,
              itemTextColor: isDark ? "#fff" : "#111",
              itemDirection: 'left-to-right',
              itemOpacity: 1,
              symbolSize: 18,
              symbolShape: 'circle',
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemTextColor: isDark ? "#fff" : "#111",
                  }
                }
              ]
            }
          ]}
          layers={["arcs", "arcLabels", "arcLinkLabels", (props) => CenteredMetric({ ...props, isDark })]}
          theme={{
            fontFamily: 'Inter, sans-serif',
            tooltip: {
              container: {
                fontSize: 16,
                fontWeight: 500,
                borderRadius: 12,
                color: isDark ? '#fff' : '#222',
                background: isDark ? '#222' : '#fff',
              },
            },
            labels: {
              text: {
                fontWeight: 700,
                fontSize: 12,
                // Remove fill here, handled by arcLabelsTextColor
              },
            },
          }}
          animate={true}
          motionConfig="gentle"
        />
      </div>
    </div>
  );
};

export default PieChartComponent;
