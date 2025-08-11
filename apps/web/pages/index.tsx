import React from 'react';
import { Layout } from '@/components/Layout';

const HomePage: React.FC = () => {
  return (
    <Layout title="Dashboard">
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Welcome to Goldleaves
        </h2>
        <p className="text-gray-600 mb-4">
          Your AI-augmented legal document platform dashboard.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-900">Quick Actions</h3>
            <p className="text-blue-700 text-sm">Upload and analyze documents</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-900">Recent Activity</h3>
            <p className="text-green-700 text-sm">View your latest document processing</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-semibold text-purple-900">Usage Stats</h3>
            <p className="text-purple-700 text-sm">Monitor your API usage and costs</p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HomePage;