'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Description as DocumentIcon,
  Chat as ChatIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Analytics as AnalyticsIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';

// Mock analytics data - replace with actual API integration
interface AnalyticsData {
  period: string;
  totalMembers: number;
  activeMembers: number;
  totalDocuments: number;
  documentsThisPeriod: number;
  totalConversations: number;
  conversationsThisPeriod: number;
  storageUsed: number; // in MB
  storageLimit: number; // in MB
  topDocuments: Array<{
    id: string;
    name: string;
    uploads: number;
    conversations: number;
  }>;
  memberActivity: Array<{
    name: string;
    uploads: number;
    conversations: number;
    lastActive: string;
  }>;
  monthlyStats: Array<{
    month: string;
    documents: number;
    conversations: number;
    members: number;
  }>;
}

const mockAnalytics: AnalyticsData = {
  period: 'Last 30 Days',
  totalMembers: 12,
  activeMembers: 8,
  totalDocuments: 156,
  documentsThisPeriod: 23,
  totalConversations: 1847,
  conversationsThisPeriod: 342,
  storageUsed: 2400, // 2.4 GB
  storageLimit: 10000, // 10 GB
  topDocuments: [
    {
      id: '1',
      name: 'Product Requirements Document.pdf',
      uploads: 15,
      conversations: 89,
    },
    {
      id: '2',
      name: 'API Documentation.md',
      uploads: 8,
      conversations: 67,
    },
    {
      id: '3',
      name: 'Meeting Notes - Q4 Planning.docx',
      uploads: 12,
      conversations: 45,
    },
  ],
  memberActivity: [
    {
      name: 'John Doe',
      uploads: 8,
      conversations: 45,
      lastActive: '2024-11-16',
    },
    {
      name: 'Jane Smith',
      uploads: 5,
      conversations: 32,
      lastActive: '2024-11-15',
    },
    {
      name: 'Mike Johnson',
      uploads: 10,
      conversations: 28,
      lastActive: '2024-11-14',
    },
  ],
  monthlyStats: [
    { month: 'Sep 2024', documents: 18, conversations: 234, members: 10 },
    { month: 'Oct 2024', documents: 25, conversations: 298, members: 11 },
    { month: 'Nov 2024', documents: 23, conversations: 342, members: 12 },
  ],
};

export default function OrgAnalyticsPage() {
  const [analytics] = useState<AnalyticsData>(mockAnalytics);
  const [timePeriod, setTimePeriod] = useState('30days');

  const formatStorage = (mb: number) => {
    if (mb < 1000) {
      return `${mb} MB`;
    }
    return `${(mb / 1000).toFixed(1)} GB`;
  };

  const getStoragePercentage = () => {
    return (analytics.storageUsed / analytics.storageLimit) * 100;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <div>
          <Typography variant="h4" component="h1" gutterBottom>
            Organization Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Insights into your organization's usage and activity
          </Typography>
        </div>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Period</InputLabel>
            <Select
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value)}
              label="Time Period"
            >
              <MenuItem value="7days">Last 7 Days</MenuItem>
              <MenuItem value="30days">Last 30 Days</MenuItem>
              <MenuItem value="90days">Last 90 Days</MenuItem>
              <MenuItem value="1year">Last Year</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {/* TODO: Implement analytics export */}}
          >
            Export Report
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon sx={{ fontSize: 40, mb: 1, color: 'primary.main' }} />
              <Typography variant="h4" component="div">
                {analytics.activeMembers}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Members
              </Typography>
              <Typography variant="caption" color="success.main">
                {analytics.activeMembers} of {analytics.totalMembers} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <DocumentIcon sx={{ fontSize: 40, mb: 1, color: 'secondary.main' }} />
              <Typography variant="h4" component="div">
                {analytics.documentsThisPeriod}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Documents Added
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {analytics.totalDocuments} total documents
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <ChatIcon sx={{ fontSize: 40, mb: 1, color: 'info.main' }} />
              <Typography variant="h4" component="div">
                {analytics.conversationsThisPeriod}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Conversations
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {analytics.totalConversations} total conversations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AnalyticsIcon sx={{ fontSize: 40, mr: 1, color: 'success.main' }} />
                <Box>
                  <Typography variant="h6" component="div">
                    Storage Used
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatStorage(analytics.storageUsed)} of {formatStorage(analytics.storageLimit)}
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={getStoragePercentage()}
                sx={{ height: 8, borderRadius: 1 }}
                color={getStoragePercentage() > 80 ? 'error' : 'primary'}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {getStoragePercentage().toFixed(1)}% used
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Tables */}
      <Grid container spacing={3}>
        {/* Top Documents */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Active Documents
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Document</TableCell>
                      <TableCell align="right">Uploads</TableCell>
                      <TableCell align="right">Conversations</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analytics.topDocuments.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {doc.name}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={doc.uploads}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={doc.conversations}
                            size="small"
                            color="secondary"
                            variant="outlined"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Member Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Member Activity
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Member</TableCell>
                      <TableCell align="right">Uploads</TableCell>
                      <TableCell align="right">Conversations</TableCell>
                      <TableCell align="right">Last Active</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analytics.memberActivity.map((member, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="body2">
                            {member.name}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {member.uploads}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {member.conversations}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(member.lastActive)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Monthly Trends */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Trends
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Month</TableCell>
                      <TableCell align="right">Documents Added</TableCell>
                      <TableCell align="right">Conversations</TableCell>
                      <TableCell align="right">Active Members</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analytics.monthlyStats.map((stat, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <CalendarIcon sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
                            <Typography variant="body2">
                              {stat.month}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {stat.documents}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {stat.conversations}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {stat.members}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Implementation Notice */}
      <Alert severity="info" sx={{ mt: 3 }}>
        This analytics dashboard shows sample data. Integration with real analytics data from the backend is pending.
        Charts and advanced visualizations will be added in future updates.
      </Alert>
    </Box>
  );
}