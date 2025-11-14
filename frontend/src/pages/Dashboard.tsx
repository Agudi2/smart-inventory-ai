import { useQuery } from '@tanstack/react-query';
import DashboardLayout from '../components/DashboardLayout';
import MetricsCard from '../components/MetricsCard';
import DashboardCharts from '../components/DashboardCharts';
import { metricsService } from '../services/metricsService';
import {
  CubeIcon,
  ExclamationTriangleIcon,
  BellAlertIcon,
  BuildingStorefrontIcon,
} from '@heroicons/react/24/outline';
import { MetricsCardSkeleton } from '../components/LoadingSkeleton';
import ErrorState from '../components/ErrorState';

export default function Dashboard() {
  const { data: metrics, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: metricsService.getDashboardMetrics,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back!</h1>
          <p className="mt-1 text-sm text-gray-600">
            Here's what's happening with your inventory today.
          </p>
        </div>

        {/* Metrics Cards */}
        {error ? (
          <ErrorState
            title="Failed to Load Dashboard Metrics"
            message="We couldn't load your dashboard data. Please try again."
            onRetry={() => refetch()}
          />
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {isLoading ? (
              <>
                <MetricsCardSkeleton />
                <MetricsCardSkeleton />
                <MetricsCardSkeleton />
                <MetricsCardSkeleton />
              </>
            ) : (
              <>
                <MetricsCard
                  title="Total Products"
                  value={metrics?.total_products || 0}
                  icon={<CubeIcon className="h-6 w-6 text-primary-600" />}
                  loading={false}
                />
                <MetricsCard
                  title="Low Stock Items"
                  value={metrics?.low_stock_count || 0}
                  icon={<ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />}
                  loading={false}
                />
                <MetricsCard
                  title="Active Alerts"
                  value={metrics?.active_alerts || 0}
                  icon={<BellAlertIcon className="h-6 w-6 text-red-600" />}
                  loading={false}
                />
                <MetricsCard
                  title="Total Vendors"
                  value={metrics?.total_vendors || 0}
                  icon={<BuildingStorefrontIcon className="h-6 w-6 text-blue-600" />}
                  loading={false}
                />
              </>
            )}
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
              <CubeIcon className="h-5 w-5 mr-2 text-gray-400" />
              Add New Product
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
              <BuildingStorefrontIcon className="h-5 w-5 mr-2 text-gray-400" />
              Add New Vendor
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
              <BellAlertIcon className="h-5 w-5 mr-2 text-gray-400" />
              View All Alerts
            </button>
          </div>
        </div>

        {/* Data Visualization Charts */}
        <DashboardCharts />
      </div>
    </DashboardLayout>
  );
}
