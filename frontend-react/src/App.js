import React, { useState, useEffect } from 'react';
import './App.css';
import ThreeColumnLayout from './components/Layout/ThreeColumnLayout';
import { checkBackendHealth } from './services/api';

function App() {
    const [backendHealthy, setBackendHealthy] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkHealth = async () => {
            try {
                const healthy = await checkBackendHealth();
                setBackendHealthy(healthy);
            } catch (error) {
                console.error('Backend health check failed:', error);
                setBackendHealthy(false);
            } finally {
                setLoading(false);
            }
        };

        checkHealth();
        // Check health every 2 minutes (less aggressive)
        const interval = setInterval(checkHealth, 120000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <h2 className="text-xl font-semibold text-gray-700">Starting PDF Analysis Workbench...</h2>
                    <p className="text-gray-500 mt-2">Checking backend connection</p>
                </div>
            </div>
        );
    }

    if (!backendHealthy) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="max-w-md mx-auto text-center bg-white p-8 rounded-lg shadow-lg">
                    <div className="text-red-500 text-6xl mb-4">⚠️</div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Backend Not Available</h2>
                    <p className="text-gray-600 mb-6">
                        The FastAPI backend is not running. Please start it first:
                    </p>
                    <div className="bg-gray-100 p-4 rounded-lg text-left font-mono text-sm">
                        <div className="text-gray-800">conda activate ./.conda</div>
                        <div className="text-gray-800">python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000</div>
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-6 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
                    >
                        🔄 Retry Connection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            <ThreeColumnLayout />
        </div>
    );
}

export default App;
