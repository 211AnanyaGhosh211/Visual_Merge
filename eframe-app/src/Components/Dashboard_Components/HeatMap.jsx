import React, { useState, useEffect } from 'react';

const HourlyHeatmap = () => {
  const [exceptionData, setExceptionData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoveredCell, setHoveredCell] = useState(null);
  const [totalExceptions, setTotalExceptions] = useState(0);
  const [maxExceptions, setMaxExceptions] = useState(0);

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Fetch exception data from backend
  const fetchExceptionData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://127.0.0.1:5000/api/plot-exceptions', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Process the data to create hour-day matrix
      const processedData = {};
      let total = 0;
      let max = 0;

      // Initialize the data structure
      dayNames.forEach(day => {
        processedData[day] = {};
        hours.forEach(hour => {
          processedData[day][hour] = 0;
        });
      });

      if (data.x && data.y && Array.isArray(data.x) && Array.isArray(data.y)) {
        data.x.forEach((timestamp, index) => {
          const count = data.y[index] || 0;
          const date = new Date(timestamp);
          
          // Get day of week (0 = Sunday, 1 = Monday, etc.)
          const dayOfWeek = date.getDay();
          const dayName = dayNames[dayOfWeek];
          
          // Get hour (0-23)
          const hour = date.getHours();
          
          // Add to the count for this day-hour combination
          processedData[dayName][hour] += count;
          total += count;
          
          // Track maximum for color scaling
          max = Math.max(max, processedData[dayName][hour]);
        });
      }

      setExceptionData(processedData);
      setTotalExceptions(total);
      setMaxExceptions(max);
      
    } catch (err) {
      console.error('Error fetching exception data:', err);
      setError(err.message);
      setExceptionData({});
      setTotalExceptions(0);
      setMaxExceptions(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptionData();
  }, []);

  // Get color intensity based on exception count
  const getColorIntensity = (count) => {
    if (count === 0) return 0;
    if (maxExceptions === 0) return 1;
    return Math.min(count / maxExceptions, 1);
  };

  // Get color class based on intensity with dark mode support
  const getColorClass = (count) => {
    const intensity = getColorIntensity(count);
    
    if (intensity === 0) return 'bg-gray-100 dark:bg-gray-800';
    if (intensity <= 0.2) return 'bg-yellow-100 dark:bg-yellow-900/30';
    if (intensity <= 0.4) return 'bg-yellow-300 dark:bg-yellow-800/50';
    if (intensity <= 0.6) return 'bg-yellow-500 dark:bg-yellow-700';
    if (intensity <= 0.8) return 'bg-yellow-700 dark:bg-yellow-600';
    return 'bg-yellow-900 dark:bg-yellow-500';
  };

  // Format hour for display
  const formatHour = (hour) => {
    if (hour === 0) return '12 AM';
    if (hour < 12) return `${hour} AM`;
    if (hour === 12) return '12 PM';
    return `${hour - 12} PM`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-2 sm:p-4 lg:p-6 rounded-lg">
      <div className="max-w-full w-full mx-auto">
        
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Exception Heatmap</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm sm:text-base">Hourly exception patterns by day of week</p>
            </div>
            <div className="text-center sm:text-right">
              <div className="text-xl sm:text-2xl font-bold text-red-600 dark:text-red-400">{totalExceptions}</div>
              <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Total Exceptions</div>
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <div className="flex">
              <div className="text-red-600 dark:text-red-400 text-xs sm:text-sm">
                <strong>Error loading data:</strong> {error}
              </div>
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {loading && (
          <div className="mb-4 sm:mb-6 flex justify-center">
            <div className="inline-flex items-center px-3 sm:px-4 py-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
              <div className="animate-spin rounded-full h-3 w-3 sm:h-4 sm:w-4 border-b-2 border-red-600 dark:border-red-400 mr-2"></div>
              Loading exception data...
            </div>
          </div>
        )}

        {/* Heatmap */}
        <div className="max-w-full w-full bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3 sm:p-4 lg:p-6 overflow-x-auto">
          
          {/* Legend */}
          <div className="mb-4 sm:mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
              <span className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">Exception Intensity:</span>
              <div className="flex items-center gap-1 sm:gap-2 text-xs text-gray-600 dark:text-gray-400">
                <span>Low</span>
                <div className="flex gap-0.5 sm:gap-1">
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-gray-100 dark:bg-gray-800"></div>
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-100 dark:bg-yellow-900/30"></div>
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-300 dark:bg-yellow-800/50"></div>
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-500 dark:bg-yellow-700"></div>
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-700 dark:bg-yellow-600"></div>
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-900 dark:bg-yellow-500"></div>
                </div>
                <span>High</span>
              </div>
            </div>
            <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
              Max: {maxExceptions} exceptions in an hour
            </div>
          </div>

          {/* Heatmap Grid */}
          <div className="max-w-full w-full min-w-[600px] ">
            
            {/* Day headers */}
            <div className="flex mb-2">
              <div className="w-12 sm:w-16 flex-shrink-0"></div> {/* Space for hour labels */}
              {dayNames.map(day => (
                <div key={day} className="flex-1 text-center text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 px-0 sm:px-0">
                  {day.slice(0, 3)}
                </div>
              ))}
            </div>

            {/* Hour rows */}
            {hours.map(hour => (
              <div key={hour} className="flex">
                {/* Hour label */}
                <div className="w-12 sm:w-16 flex-shrink-0 text-right pr-2 sm:pr-3 text-xs text-gray-600 dark:text-gray-400 flex items-center justify-end">
                  <span className="hidden sm:inline">{formatHour(hour)}</span>
                  <span className="sm:hidden">{hour}</span>
                </div>
                
                {/* Day cells */}
                {dayNames.map(day => {
                  const count = exceptionData[day]?.[hour] || 0;
                  const cellId = `${day}-${hour}`;
                  const isHovered = hoveredCell === cellId;
                  
                  return (
                    <div
                      key={cellId}
                      className={`flex-1 h-6 sm:h-8 w-6 sm:w-8 cursor-pointer transition-all duration-200 flex items-center justify-center text-xs font-medium ${
                        getColorClass(count)
                      } ${isHovered ? 'ring-2 ring-blue-400 dark:ring-blue-500 ring-offset-1 dark:ring-offset-gray-800' : ''} ${
                        loading ? 'opacity-50' : ''
                      }`}
                      onClick={() => setHoveredCell(cellId)}
                      onMouseLeave={() => setHoveredCell(null)}
                      title={`${count} exceptions on ${day} at ${formatHour(hour)}`}
                    >
                      {count > 0 && (
                        <span className={count > maxExceptions * 0.6 ? 'text-white dark:text-white' : 'text-gray-800 dark:text-gray-200'}>
                          {count}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Hover tooltip */}
          {hoveredCell && !loading && (
            <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-800 dark:bg-gray-700 text-white text-xs sm:text-sm rounded-md max-w-xs">
              {(() => {
                const [day, hour] = hoveredCell.split('-');
                const count = exceptionData[day]?.[parseInt(hour)] || 0;
                return (
                  <div>
                    <div className="font-semibold">
                      {count} exception{count !== 1 ? 's' : ''}
                    </div>
                    <div className="text-gray-300 dark:text-gray-400">
                      {day} at {formatHour(parseInt(hour))}
                    </div>
                    {count > 0 && (
                      <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {((count / maxExceptions) * 100).toFixed(1)}% of peak activity
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </div>

        {/* Insights Panel */}
        {!loading && Object.keys(exceptionData).length > 0 && (
          <div className="mt-4 sm:mt-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3 sm:p-4 lg:p-6">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">Key Insights</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              
              {/* Peak Hour */}
              <div className="bg-red-50 dark:bg-red-900/20 p-3 sm:p-4 rounded-lg">
                <h4 className="font-medium text-red-800 dark:text-red-300 mb-2 text-sm sm:text-base">Peak Exception Time</h4>
                <div className="text-xs sm:text-sm text-red-700 dark:text-red-400">
                  {(() => {
                    let maxCount = 0;
                    let peakDay = '';
                    let peakHour = 0;
                    
                    Object.entries(exceptionData).forEach(([day, hours]) => {
                      Object.entries(hours).forEach(([hour, count]) => {
                        if (count > maxCount) {
                          maxCount = count;
                          peakDay = day;
                          peakHour = parseInt(hour);
                        }
                      });
                    });
                    
                    return maxCount > 0 
                      ? `${peakDay} at ${formatHour(peakHour)} (${maxCount} exceptions)`
                      : 'No data available';
                  })()}
                </div>
              </div>

              {/* Busiest Day */}
              <div className="bg-orange-50 dark:bg-orange-900/20 p-3 sm:p-4 rounded-lg">
                <h4 className="font-medium text-orange-800 dark:text-orange-300 mb-2 text-sm sm:text-base">Busiest Day</h4>
                <div className="text-xs sm:text-sm text-orange-700 dark:text-orange-400">
                  {(() => {
                    const dayTotals = {};
                    Object.entries(exceptionData).forEach(([day, hours]) => {
                      dayTotals[day] = Object.values(hours).reduce((sum, count) => sum + count, 0);
                    });
                    
                    const busiestDay = Object.entries(dayTotals).reduce((max, [day, total]) => 
                      total > max.total ? { day, total } : max, { day: '', total: 0 });
                    
                    return busiestDay.total > 0 
                      ? `${busiestDay.day} (${busiestDay.total} exceptions)`
                      : 'No data available';
                  })()}
                </div>
              </div>

              {/* Work Hours Activity */}
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 sm:p-4 rounded-lg">
                <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2 text-sm sm:text-base">Work Hours (9 AM - 5 PM)</h4>
                <div className="text-xs sm:text-sm text-blue-700 dark:text-blue-400">
                  {(() => {
                    let workHoursTotal = 0;
                    Object.values(exceptionData).forEach(dayData => {
                      for (let hour = 9; hour <= 17; hour++) {
                        workHoursTotal += dayData[hour] || 0;
                      }
                    });
                    
                    const percentage = totalExceptions > 0 
                      ? ((workHoursTotal / totalExceptions) * 100).toFixed(1)
                      : 0;
                    
                    return `${workHoursTotal} exceptions (${percentage}% of total)`;
                  })()}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HourlyHeatmap;