import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import OptionScatterChart from './components/OptionScatterChart';
import axios from 'axios';

function App() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [optionData, setOptionData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [endpoint, setEndpoint] = useState('top-volatile-options');

  const endpoints = [
    { value: 'top-volatile-options', label: 'Top Volatile Options' },
    { value: 'only-buyers', label: 'Only Buyers Options' },
    { value: 'top-volatile-options-all', label: 'All F&O Stocks (No Symbol Required)' }
  ];

  const fetchOptionData = async () => {
    setLoading(true);
    setError('');

    try {
      let url = `/api/v1/analytics/${endpoint}`;
      if (endpoint !== 'top-volatile-options-all') {
        url += `?symbol=${symbol}`;
      }

      const response = await axios.get(url);
      setOptionData(response.data.data || []);
    } catch (err) {
      setError(`Failed to fetch data: ${err.response?.data?.detail || err.message}`);
      setOptionData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (endpoint === 'top-volatile-options-all' || symbol) {
      fetchOptionData();
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchOptionData();
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        Option Screener Analytics
      </Typography>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Analysis Type</InputLabel>
                  <Select
                    value={endpoint}
                    label="Analysis Type"
                    onChange={(e) => setEndpoint(e.target.value)}
                  >
                    {endpoints.map((ep) => (
                      <MenuItem key={ep.value} value={ep.value}>
                        {ep.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {endpoint !== 'top-volatile-options-all' && (
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Stock Symbol"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    placeholder="Enter symbol (e.g., RELIANCE)"
                    required
                  />
                </Grid>
              )}

              <Grid item xs={12} md={4}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Analyze Options'}
                </Button>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress size={60} />
        </Box>
      )}

      {!loading && optionData.length > 0 && (
        <Grid container spacing={4}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h5" gutterBottom>
                  Strike Price vs Implied Volatility
                </Typography>
                <OptionScatterChart
                  data={optionData}
                  xField="strikePrice"
                  yField="impliedVolatility"
                  title="Strike Price vs Implied Volatility"
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Strike Gap vs Premium Percentage
                </Typography>
                <OptionScatterChart
                  data={optionData}
                  xField="strikeGapPercentage"
                  yField="premiumPercentage"
                  title="Strike Gap % vs Premium %"
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Volume vs Implied Volatility
                </Typography>
                <OptionScatterChart
                  data={optionData}
                  xField="totalTradedVolume"
                  yField="impliedVolatility"
                  title="Volume vs Implied Volatility"
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {!loading && optionData.length === 0 && !error && (
        <Alert severity="info">
          No option data available. Try analyzing a different symbol.
        </Alert>
      )}
    </Container>
  );
}

export default App;
