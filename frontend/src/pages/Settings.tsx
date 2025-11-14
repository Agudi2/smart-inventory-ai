import DashboardLayout from '../components/DashboardLayout';
import { Cog6ToothIcon } from '@heroicons/react/24/outline';

export default function Settings() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="mt-1 text-sm text-gray-600">
            Configure your inventory system preferences
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-12">
          <div className="text-center">
            <Cog6ToothIcon className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">System Settings</h3>
            <p className="mt-2 text-sm text-gray-500">
              This page will allow you to configure alert thresholds, notifications, and other preferences.
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Coming soon in the next task...
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
