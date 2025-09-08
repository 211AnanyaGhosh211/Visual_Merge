import React from 'react';

const CameraTable = ({ cameras }) => {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-neutral-800">
      <table className="w-full border-collapse text-sm md:text-base">
        <thead className="sticky top-0 z-10">
          <tr>
            <th className="bg-yellow-300 text-gray-800 font-bold px-2 py-2 md:px-4 md:py-3 whitespace-nowrap">Camera ID</th>
            <th className="bg-yellow-300 text-gray-800 font-bold px-2 py-2 md:px-4 md:py-3 whitespace-nowrap">Camera Name</th>
            <th className="bg-yellow-300 text-gray-800 font-bold px-2 py-2 md:px-4 md:py-3 whitespace-nowrap">Zone Name</th>
            <th className="bg-yellow-300 text-gray-800 font-bold px-2 py-2 md:px-4 md:py-3 whitespace-nowrap">IP Address</th>
            <th className="bg-yellow-300 text-gray-800 font-bold px-2 py-2 md:px-4 md:py-3 whitespace-nowrap">Streaming URL</th>
            <th className="bg-yellow-300 text-gray-800 font-bold px-2 py-2 md:px-4 md:py-3 whitespace-nowrap">Playback URL</th>
          </tr>
        </thead>
        <tbody>
          {cameras.length > 0 ? cameras.map((camera, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white dark:bg-neutral-900' : 'bg-gray-50 dark:bg-neutral-800'}>
              <td className="border-t border-gray-200 dark:border-neutral-800 px-2 py-2 md:px-4 md:py-3 dark:text-white whitespace-nowrap">{camera.Camera_id}</td>
              <td className="border-t border-gray-200 dark:border-neutral-800 px-2 py-2 md:px-4 md:py-3 dark:text-white whitespace-nowrap">{camera.Camera_name}</td>
              <td className="border-t border-gray-200 dark:border-neutral-800 px-2 py-2 md:px-4 md:py-3 dark:text-white whitespace-nowrap">{camera.Zone_name}</td>
              <td className="border-t border-gray-200 dark:border-neutral-800 px-2 py-2 md:px-4 md:py-3 dark:text-white whitespace-nowrap">{camera.IP_address}</td>
              <td className="border-t border-gray-200 dark:border-neutral-800 px-2 py-2 md:px-4 md:py-3 dark:text-white whitespace-nowrap">{camera.Streaming_URL}</td>
              <td className="border-t border-gray-200 dark:border-neutral-800 px-2 py-2 md:px-4 md:py-3 dark:text-white whitespace-nowrap">{camera.Playback_URL}</td>
            </tr>
          )) : (
            <tr><td colSpan={6} className="text-center py-4 text-gray-400">No cameras found.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default CameraTable; 