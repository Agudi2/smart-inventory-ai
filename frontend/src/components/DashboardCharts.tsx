import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { chartService } from '../services/chartService';
import { ChartSkeleton } from './LoadingSkeleton';
import { InlineError } from './ErrorState';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function DashboardCharts() {
  // Fetch data for all charts
  const { data: stockLevelData, isLoading: stockLevelLoading, error: stockLevelError, refetch: refetchStockLevel } = useQuery({
    queryKey: ['stock-level-overview'],
    queryFn: chartService.getStockLevelOverview,
    refetchInterval: 60000, // Refetch every minute
  });

  const { data: consumptionData, isLoading: consumptionLoading, error: consumptionError, refetch: refetchConsumption } = useQuery({
    queryKey: ['consumption-trend'],
    queryFn: () => chartService.getConsumptionTrend(30),
    refetchInterval: 60000,
  });

  const { data: categoryData, isLoading: categoryLoading } = useQuery({
    queryKey: ['category-distribution'],
    queryFn: chartService.getCategoryDistribution,
    refetchInterval: 60000,
  });

  const { data: alertData, isLoading: alertLoading } = useQuery({
    queryKey: ['alert-trend'],
    queryFn: () => chartService.getAlertTrend(30),
    refetchInterval: 60000,
  });

  return (
    <div className="space-y-6">
      {/* Stock Level Overview Chart */}
      {stockLevelLoading ? (
        <ChartSkeleton />
      ) : stockLevelError ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Stock Level Overview
          </h2>
          <InlineError
            message="Failed to load stock level data"
            onRetry={() => refetchStockLevel()}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Stock Level Overview
          </h2>
          {stockLevelData && stockLevelData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stockLevelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" name="Products" radius={[8, 8, 0, 0]}>
                  {stockLevelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No stock data available
            </div>
          )}
        </div>
      )}

      {/* Consumption Trend Chart */}
      {consumptionLoading ? (
        <ChartSkeleton />
      ) : consumptionError ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Consumption Trend (Last 30 Days)
          </h2>
          <InlineError
            message="Failed to load consumption trend data"
            onRetry={() => refetchConsumption()}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Consumption Trend (Last 30 Days)
          </h2>
          {consumptionData && consumptionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={consumptionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleDateString();
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="additions"
                  stroke="#10b981"
                  name="Stock Added"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="removals"
                  stroke="#ef4444"
                  name="Stock Removed"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="net"
                  stroke="#3b82f6"
                  name="Net Change"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No consumption data available
            </div>
          )}
        </div>
      )}

      {/* Category Distribution and Alert Trend - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Inventory by Category
          </h2>
          {categoryLoading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : categoryData && categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) =>
                    `${entry.category}: ${((entry.percent || 0) * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((_entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No category data available
            </div>
          )}
        </div>

        {/* Alert Frequency Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Alert Trends (Last 30 Days)
          </h2>
          {alertLoading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : alertData && alertData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={alertData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleDateString();
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="low_stock"
                  stroke="#f59e0b"
                  name="Low Stock Alerts"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="predicted_depletion"
                  stroke="#ef4444"
                  name="Depletion Alerts"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="total"
                  stroke="#8b5cf6"
                  name="Total Alerts"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No alert data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
