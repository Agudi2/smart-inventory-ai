import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BellAlertIcon,
  CheckCircleIcon,
  XMarkIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { ExclamationTriangleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import { alertService } from '../services/alertService';
import { formatDateTime } from '../utils/format';
import { ListSkeleton } from './LoadingSkeleton';
import ErrorState from './ErrorState';

interface AlertsPanelProps {
  showFilters?: boolean;
}

export default function AlertsPanel({ showFilters = true }: AlertsPanelProps) {
  const queryClient = useQueryClient();
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('active');

  // Fetch alerts
  const { data: alerts = [], isLoading, error } = useQuery({
    queryKey: ['alerts'],
    queryFn: alertService.getAlerts,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Acknowledge alert mutation
  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) => alertService.acknowledgeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert acknowledged');
    },
    onError: () => {
      toast.error('Failed to acknowledge alert');
    },
  });

  // Resolve alert mutation
  const resolveMutation = useMutation({
    mutationFn: (alertId: string) => alertService.resolveAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert resolved');
    },
    onError: () => {
      toast.error('Failed to resolve alert');
    },
  });

  // Filter alerts
  const filteredAlerts = useMemo(() => {
    let filtered = [...alerts];

    // Filter by status
    if (statusFilter) {
      filtered = filtered.filter((alert) => alert.status === statusFilter);
    }

    // Filter by type
    if (typeFilter) {
      filtered = filtered.filter((alert) => alert.alert_type === typeFilter);
    }

    // Filter by severity
    if (severityFilter) {
      filtered = filtered.filter((alert) => alert.severity === severityFilter);
    }

    // Sort by created_at (newest first)
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return filtered;
  }, [alerts, typeFilter, severityFilter, statusFilter]);

  // Get severity badge
  const getSeverityBadge = (severity: string) => {
    const badges = {
      warning: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800',
    };
    const labels = {
      warning: 'Warning',
      critical: 'Critical',
    };
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          badges[severity as keyof typeof badges] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {labels[severity as keyof typeof labels] || severity}
      </span>
    );
  };

  // Get alert type label
  const getAlertTypeLabel = (type: string) => {
    const labels = {
      low_stock: 'Low Stock',
      predicted_depletion: 'Predicted Depletion',
    };
    return labels[type as keyof typeof labels] || type;
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    const badges = {
      active: 'bg-blue-100 text-blue-800',
      acknowledged: 'bg-purple-100 text-purple-800',
      resolved: 'bg-green-100 text-green-800',
    };
    const labels = {
      active: 'Active',
      acknowledged: 'Acknowledged',
      resolved: 'Resolved',
    };
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    if (severity === 'critical') {
      return <ExclamationCircleIcon className="w-6 h-6 text-red-500" />;
    }
    return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-500" />;
  };

  // Handle acknowledge
  const handleAcknowledge = (alertId: string) => {
    acknowledgeMutation.mutate(alertId);
  };

  // Handle resolve
  const handleResolve = (alertId: string) => {
    resolveMutation.mutate(alertId);
  };

  if (isLoading) {
    return <ListSkeleton items={5} />;
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to Load Alerts"
        message="We couldn't load your alerts. Please check your connection and try again."
        onRetry={() => queryClient.invalidateQueries({ queryKey: ['alerts'] })}
      />
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Filters */}
      {showFilters && (
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-3">
            <FunnelIcon className="w-5 h-5 text-gray-400" />
            <h3 className="text-sm font-medium text-gray-700">Filters</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Status Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Alert Type
              </label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                <option value="low_stock">Low Stock</option>
                <option value="predicted_depletion">Predicted Depletion</option>
              </select>
            </div>

            {/* Severity Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Severity
              </label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">All Severities</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Results count */}
          <div className="mt-3 text-sm text-gray-600">
            Showing {filteredAlerts.length} of {alerts.length} alerts
          </div>
        </div>
      )}

      {/* Alerts List */}
      <div className="divide-y divide-gray-200">
        {filteredAlerts.length === 0 ? (
          <div className="p-12 text-center">
            <BellAlertIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No alerts</h3>
            <p className="mt-2 text-sm text-gray-500">
              {statusFilter || typeFilter || severityFilter
                ? 'No alerts match your current filters.'
                : 'All clear! No active alerts at the moment.'}
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className="p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start gap-4">
                {/* Severity Icon */}
                <div className="flex-shrink-0 mt-1">
                  {getSeverityIcon(alert.severity)}
                </div>

                {/* Alert Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {/* Product Info */}
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-semibold text-gray-900">
                          {alert.product_name || 'Unknown Product'}
                        </h4>
                        {alert.product_sku && (
                          <span className="text-xs text-gray-500">
                            ({alert.product_sku})
                          </span>
                        )}
                      </div>

                      {/* Alert Message */}
                      <p className="text-sm text-gray-700 mb-2">
                        {alert.message}
                      </p>

                      {/* Badges */}
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        {getSeverityBadge(alert.severity)}
                        {getStatusBadge(alert.status)}
                        <span className="text-xs text-gray-500">
                          {getAlertTypeLabel(alert.alert_type)}
                        </span>
                        {alert.current_stock !== undefined && (
                          <span className="text-xs text-gray-500">
                            Current Stock: {alert.current_stock}
                          </span>
                        )}
                      </div>

                      {/* Timestamps */}
                      <div className="text-xs text-gray-500">
                        <span>
                          Created: {formatDateTime(alert.created_at)}
                        </span>
                        {alert.acknowledged_at && (
                          <span className="ml-3">
                            Acknowledged: {formatDateTime(alert.acknowledged_at)}
                          </span>
                        )}
                        {alert.resolved_at && (
                          <span className="ml-3">
                            Resolved: {formatDateTime(alert.resolved_at)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    {alert.status !== 'resolved' && (
                      <div className="flex flex-col gap-2">
                        {alert.status === 'active' && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            disabled={acknowledgeMutation.isPending}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-100 rounded-md hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            title="Acknowledge alert"
                          >
                            <CheckCircleIcon className="w-4 h-4" />
                            Acknowledge
                          </button>
                        )}
                        <button
                          onClick={() => handleResolve(alert.id)}
                          disabled={resolveMutation.isPending}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Resolve alert"
                        >
                          <XMarkIcon className="w-4 h-4" />
                          Resolve
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
