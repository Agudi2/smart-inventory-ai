import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { type PredictionResult } from '../services/predictionService';

interface RestockPredictionChartProps {
  prediction: PredictionResult;
  reorderThreshold: number;
}

export default function RestockPredictionChart({ prediction, reorderThreshold }: RestockPredictionChartProps) {
  if (!prediction.forecast || prediction.forecast.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No forecast data available</p>
      </div>
    );
  }

  // Transform forecast data for Recharts
  const chartData = prediction.forecast.map((point) => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    stock: Math.round(point.predicted_stock * 10) / 10,
    lowerBound: point.lower_bound ? Math.round(point.lower_bound * 10) / 10 : undefined,
    upperBound: point.upper_bound ? Math.round(point.upper_bound * 10) / 10 : undefined,
  }));

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ value: 'Stock Level', angle: -90, position: 'insideLeft', style: { fontSize: '12px' } }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff', 
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '12px'
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
          />
          
          {/* Reorder threshold line */}
          <ReferenceLine 
            y={reorderThreshold} 
            stroke="#f59e0b" 
            strokeDasharray="5 5"
            label={{ value: 'Reorder Threshold', position: 'right', fill: '#f59e0b', fontSize: 11 }}
          />
          
          {/* Zero stock line */}
          <ReferenceLine 
            y={0} 
            stroke="#ef4444" 
            strokeDasharray="3 3"
          />
          
          {/* Upper bound (confidence interval) */}
          {chartData[0]?.upperBound !== undefined && (
            <Line 
              type="monotone" 
              dataKey="upperBound" 
              stroke="#93c5fd" 
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              name="Upper Bound"
            />
          )}
          
          {/* Lower bound (confidence interval) */}
          {chartData[0]?.lowerBound !== undefined && (
            <Line 
              type="monotone" 
              dataKey="lowerBound" 
              stroke="#93c5fd" 
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              name="Lower Bound"
            />
          )}
          
          {/* Predicted stock */}
          <Line 
            type="monotone" 
            dataKey="stock" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            activeDot={{ r: 5 }}
            name="Predicted Stock"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
