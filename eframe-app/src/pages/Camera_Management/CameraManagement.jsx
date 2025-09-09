import React, { useEffect, useState } from 'react';
import Header from '../../components/Camera_Management_Components/Header';
import Footer from '../../components/Camera_Management_Components/Footer';
import CameraTable from '../../components/Camera_Management_Components/CameraTable';
import InsertCameraModal from '../../components/Camera_Management_Components/InsertCameraModal';
import DeleteCameraModal from '../../components/Camera_Management_Components/DeleteCameraModal';
import CameraActions from '../../components/Camera_Management_Components/CameraActions';
import { FaVideo } from 'react-icons/fa';

const CameraManagement = () => {
  const [cameras, setCameras] = useState([]);
  const [showInsertModal, setShowInsertModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [insertForm, setInsertForm] = useState({
    cameraID: '',
    cameraName: '',
    zoneName: '',
    ipAddress: '',
    streamingURL: '',
    playbackURL: '',
  });
  const [deleteCameraID, setDeleteCameraID] = useState('');

  useEffect(() => {
    fetchCameras();
  }, []);

  const fetchCameras = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5000/api/cameras');
      const data = await res.json();
      console.log('Received camera data:', data);
      setCameras(data);
    } catch (err) {
      console.error('Error fetching cameras:', err);
      setCameras([]);
    }
  };

  const handleInsertChange = (e) => {
    setInsertForm({ ...insertForm, [e.target.name]: e.target.value });
  };

  const handleInsertSubmit = async (e) => {
    e.preventDefault();
    try {
      await fetch('http://127.0.0.1:5000/api/set_camera', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          camera_id: insertForm.cameraID,
          camera_name: insertForm.cameraName,
          zone_name: insertForm.zoneName,
          ip_address: insertForm.ipAddress,
          streaming_url: insertForm.streamingURL,
          playback_url: insertForm.playbackURL,
        }),
      });
      alert('Records Inserted Successfully');
      setShowInsertModal(false);
      fetchCameras();
    } catch (err) {
      alert('Insert failed');
    }
  };

  const handleDeleteSubmit = async (e) => {
    e.preventDefault();
    try {
      await fetch('http://127.0.0.1:5000/api/del_camera', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_id: deleteCameraID }),
      });
      alert('Records Deleted Successfully');
      setShowDeleteModal(false);
      fetchCameras();
    } catch (err) {
      alert('Delete failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 dark:from-neutral-900 dark:to-neutral-800">
      <Header title="Camera Management" subtitle="Manage your cameras and their details" />
      <main className="p-2 sm:p-4 lg:p-8 max-w-9xl mx-auto">
        <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-neutral-800 w-full max-w-full px-2 py-4 sm:px-6 sm:py-8 md:px-10 md:py-10 mt-4 sm:mt-6">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 gap-4">
            <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-800 dark:text-gray-100">
              <FaVideo className="text-yellow-500" /> Camera Management
            </h2>
            <CameraActions
              onInsert={() => setShowInsertModal(true)}
              onDelete={() => setShowDeleteModal(true)}
            />
          </div>
          <CameraTable cameras={cameras} />
        </div>

        <InsertCameraModal
          show={showInsertModal}
          onClose={() => setShowInsertModal(false)}
          formData={insertForm}
          onChange={handleInsertChange}
          onSubmit={handleInsertSubmit}
        />

        <DeleteCameraModal
          show={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          cameraID={deleteCameraID}
          onChange={(e) => setDeleteCameraID(e.target.value)}
          onSubmit={handleDeleteSubmit}
        />

        <Footer />
      </main>
    </div>
  );
};

export default CameraManagement; 