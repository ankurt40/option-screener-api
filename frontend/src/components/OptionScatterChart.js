import React from 'react';
import { ScatterChart } from '@mui/x-charts/ScatterChart';
import { Box, Typography, Chip } from '@mui/material';

const OptionScatterChart = ({ data, xField, yField, title }) => {
  // Prepare data for scatter chart
  const prepareChartData = () => {
    const ceData = [];
    const peData = [];

    data.forEach((strike, index) => {
      const xValue = strike[xField];
      const yValue = strike[yField];

      // Skip if values are null, undefined, or invalid
      if (xValue == null || yValue == null ||
          !isFinite(xValue) || !isFinite(yValue)) {
        return;
      }

      const dataPoint = {
        x: xValue,
        y: yValue,
        id: index,
        strike: strike.strikePrice,
        symbol: strike.underlying,
        type: strike.type,
        expiry: strike.expiryDate,
        iv: strike.impliedVolatility,
        premium: strike.lastPrice,
        strikeGap: strike.strikeGap,
        strikeGapPercentage: strike.strikeGapPercentage,
        premiumPercentage: strike.premiumPercentage
      };

      if (strike.type === 'CE') {
        ceData.push(dataPoint);
      } else if (strike.type === 'PE') {
        peData.push(dataPoint);
      }
    });

    return { ceData, peData };
  };

  const { ceData, peData } = prepareChartData();

  // Custom tooltip content
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box
          sx={{
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            p: 2,
            boxShadow: 2,
          }}
        >
          <Typography variant="subtitle2" gutterBottom>
            {data.symbol} - {data.strike} {data.type}
          </Typography>
          <Typography variant="body2">
            <strong>{getFieldLabel(xField)}:</strong> {formatValue(data.x, xField)}
          </Typography>
          <Typography variant="body2">
            <strong>{getFieldLabel(yField)}:</strong> {formatValue(data.y, yField)}
          </Typography>
          <Typography variant="body2">
            <strong>Premium:</strong> ₹{data.premium}
          </Typography>
          <Typography variant="body2">
            <strong>IV:</strong> {data.iv}%
          </Typography>
          <Typography variant="body2">
            <strong>Expiry:</strong> {data.expiry}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  const getFieldLabel = (field) => {
    const labels = {
      strikePrice: 'Strike Price',
      impliedVolatility: 'Implied Volatility (%)',
      strikeGapPercentage: 'Strike Gap (%)',
      premiumPercentage: 'Premium (%)',
      totalTradedVolume: 'Volume',
      openInterest: 'Open Interest',
      lastPrice: 'Last Price (₹)',
      strikeGap: 'Strike Gap (₹)'
    };
    return labels[field] || field;
  };

  const formatValue = (value, field) => {
    if (field.includes('Percentage') || field === 'impliedVolatility') {
      return `${value.toFixed(2)}%`;
    }
    if (field === 'strikePrice' || field === 'lastPrice' || field === 'strikeGap') {
      return `₹${value.toFixed(2)}`;
    }
    return value.toLocaleString();
  };

  const series = [];

  if (ceData.length > 0) {
    series.push({
      data: ceData,
      label: 'Call Options (CE)',
      id: 'ce',
      color: '#4caf50' // Green for calls
    });
  }

  if (peData.length > 0) {
    series.push({
      data: peData,
      label: 'Put Options (PE)',
      id: 'pe',
      color: '#f44336' // Red for puts
    });
  }

  if (series.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={400}>
        <Typography variant="body1" color="text.secondary">
          No valid data points to display
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" gap={1} mb={2} flexWrap="wrap">
        {ceData.length > 0 && (
          <Chip
            label={`Call Options: ${ceData.length}`}
            color="success"
            variant="outlined"
            size="small"
          />
        )}
        {peData.length > 0 && (
          <Chip
            label={`Put Options: ${peData.length}`}
            color="error"
            variant="outlined"
            size="small"
          />
        )}
        <Chip
          label={`Total Points: ${ceData.length + peData.length}`}
          variant="outlined"
          size="small"
        />
      </Box>

      <ScatterChart
        width={800}
        height={400}
        series={series}
        xAxis={[{
          label: getFieldLabel(xField),
          min: Math.min(...series.flatMap(s => s.data.map(d => d.x))) * 0.95,
          max: Math.max(...series.flatMap(s => s.data.map(d => d.x))) * 1.05
        }]}
        yAxis={[{
          label: getFieldLabel(yField),
          min: Math.min(...series.flatMap(s => s.data.map(d => d.y))) * 0.95,
          max: Math.max(...series.flatMap(s => s.data.map(d => d.y))) * 1.05
        }]}
        grid={{ horizontal: true, vertical: true }}
        tooltip={{ trigger: 'item' }}
        margin={{ left: 80, right: 80, top: 80, bottom: 80 }}
      />
    </Box>
  );
};

export default OptionScatterChart;
