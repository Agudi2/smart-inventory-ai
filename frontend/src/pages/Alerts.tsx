import DashboardLayout from '../components/DashboardLayout';
import AlertsPanel from '../components/AlertsPanel';

export default function Alerts() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="mt-1 text-sm text-gray-600">
            Monitor and manage inventory alerts for low stock and predicted depletion
          </p>
        </div>

        <AlertsPanel showFilters={true} />
      </div>
    </DashboardLayout>
  );
}
