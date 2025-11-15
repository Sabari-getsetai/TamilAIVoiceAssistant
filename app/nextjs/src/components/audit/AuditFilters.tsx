'use client';

/**
 * Advanced Audit Filters Component
 *
 * Features:
 * - Date range picker with presets
 * - Multi-select action and resource type filters
 * - User and IP address search
 * - Severity level selection
 * - Compliance framework filtering
 * - Collapsible filter sections
 * - Filter persistence and reset
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Checkbox,
  ListItemText,
  IconButton,
  Tooltip,
  Alert,
  Grid,
  Autocomplete,
} from '@mui/material';
import {
  ExpandMore,
  FilterList,
  Clear,
  CalendarToday,
  Person,
  Computer,
  Security,
  Business,
  Refresh,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

import {
  AuditFilters as IAuditFilters,
  ActionType,
  ResourceType,
  AuditSeverity,
  ComplianceTag,
  ActionTypeOptions,
  ResourceTypeOptions,
  ComplianceTagOptions,
  SeverityOptions,
  defaultAuditFilters,
} from '../../services/api/audit/auditTypes';
import {
  useActionTypes,
  useResourceTypes,
  useComplianceTags,
} from '../../services/api/audit/auditQueries';

interface AuditFiltersProps {
  filters: Partial<IAuditFilters>;
  onChange: (filters: Partial<IAuditFilters>) => void;
  onApply?: () => void;
  onReset?: () => void;
  isLoading?: boolean;
  compact?: boolean;
}

// Date range presets
const DATE_PRESETS = [
  { label: 'Today', value: 0 },
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 90 days', value: 90 },
  { label: 'Last year', value: 365 },
] as const;

export const AuditFilters: React.FC<AuditFiltersProps> = ({
  filters,
  onChange,
  onApply,
  onReset,
  isLoading = false,
  compact = false,
}) => {
  const [localFilters, setLocalFilters] = useState<Partial<IAuditFilters>>(filters);
  const [expandedSection, setExpandedSection] = useState<string | false>('datetime');

  // Fetch filter options from API
  const { data: actionTypes } = useActionTypes();
  const { data: resourceTypes } = useResourceTypes();
  const { data: complianceTags } = useComplianceTags();

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Handle filter changes
  const handleFilterChange = useCallback((key: keyof IAuditFilters, value: any) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);

    // Auto-apply in compact mode
    if (compact) {
      onChange(newFilters);
    }
  }, [localFilters, compact, onChange]);

  // Handle date preset selection
  const handleDatePreset = (days: number) => {
    const endDate = endOfDay(new Date());
    const startDate = days === 0 ? startOfDay(new Date()) : startOfDay(subDays(new Date(), days));

    const newFilters = {
      ...localFilters,
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
    };
    setLocalFilters(newFilters);

    if (compact) {
      onChange(newFilters);
    }
  };

  // Apply filters
  const handleApply = () => {
    onChange(localFilters);
    onApply?.();
  };

  // Reset filters
  const handleReset = () => {
    const resetFilters = { ...defaultAuditFilters };
    setLocalFilters(resetFilters);
    onChange(resetFilters);
    onReset?.();
  };

  // Clear specific filter
  const handleClearFilter = (key: keyof IAuditFilters) => {
    const newFilters = { ...localFilters };
    delete newFilters[key];
    setLocalFilters(newFilters);

    if (compact) {
      onChange(newFilters);
    }
  };

  // Toggle accordion section
  const handleAccordionChange = (section: string) => (
    _: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedSection(isExpanded ? section : false);
  };

  // Count active filters
  const activeFilterCount = Object.keys(localFilters).filter(
    key => localFilters[key as keyof IAuditFilters] !== undefined &&
           localFilters[key as keyof IAuditFilters] !== null &&
           localFilters[key as keyof IAuditFilters] !== ''
  ).length;

  const FilterSection: React.FC<{
    title: string;
    icon: React.ReactNode;
    section: string;
    children: React.ReactNode;
  }> = ({ title, icon, section, children }) => (
    <Accordion
      expanded={expandedSection === section}
      onChange={handleAccordionChange(section)}
      disableGutters
    >
      <AccordionSummary
        expandIcon={<ExpandMore />}
        aria-controls={`${section}-content`}
        id={`${section}-header`}
        sx={{ minHeight: 48 }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          {icon}
          <Typography variant="subtitle2">{title}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0 }}>
        {children}
      </AccordionDetails>
    </Accordion>
  );

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Card>
        <CardContent>
          {/* Filter Header */}
          <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <FilterList />
              <Typography variant="h6">Filters</Typography>
              {activeFilterCount > 0 && (
                <Chip
                  label={`${activeFilterCount} active`}
                  size="small"
                  color="primary"
                />
              )}
            </Box>
            <Tooltip title="Reset all filters">
              <IconButton onClick={handleReset} size="small">
                <Clear />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Date & Time Filters */}
          <FilterSection
            title="Date & Time"
            icon={<CalendarToday fontSize="small" />}
            section="datetime"
          >
            <Stack spacing={2}>
              {/* Date Presets */}
              <Box>
                <Typography variant="body2" color="text.secondary" mb={1}>
                  Quick Select:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {DATE_PRESETS.map(preset => (
                    <Button
                      key={preset.value}
                      size="small"
                      variant="outlined"
                      onClick={() => handleDatePreset(preset.value)}
                    >
                      {preset.label}
                    </Button>
                  ))}
                </Stack>
              </Box>

              {/* Custom Date Range */}
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <DatePicker
                    label="Start Date"
                    value={localFilters.start_date ? new Date(localFilters.start_date) : null}
                    onChange={(date) =>
                      handleFilterChange('start_date', date?.toISOString())
                    }
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                        InputProps: {
                          endAdornment: localFilters.start_date && (
                            <IconButton
                              size="small"
                              onClick={() => handleClearFilter('start_date')}
                            >
                              <Clear fontSize="small" />
                            </IconButton>
                          ),
                        },
                      },
                    }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <DatePicker
                    label="End Date"
                    value={localFilters.end_date ? new Date(localFilters.end_date) : null}
                    onChange={(date) =>
                      handleFilterChange('end_date', date?.toISOString())
                    }
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                        InputProps: {
                          endAdornment: localFilters.end_date && (
                            <IconButton
                              size="small"
                              onClick={() => handleClearFilter('end_date')}
                            >
                              <Clear fontSize="small" />
                            </IconButton>
                          ),
                        },
                      },
                    }}
                  />
                </Grid>
              </Grid>
            </Stack>
          </FilterSection>

          {/* Action & Resource Filters */}
          <FilterSection
            title="Actions & Resources"
            icon={<Security fontSize="small" />}
            section="actions"
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Action Types</InputLabel>
                  <Select
                    multiple
                    value={localFilters.action_types || []}
                    onChange={(e) =>
                      handleFilterChange('action_types', e.target.value)
                    }
                    input={<OutlinedInput label="Action Types" />}
                    renderValue={(selected) => (
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {(selected as ActionType[]).map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {actionTypes?.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        <Checkbox
                          checked={(localFilters.action_types || []).indexOf(option.value as ActionType) > -1}
                        />
                        <ListItemText primary={option.name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Resource Types</InputLabel>
                  <Select
                    multiple
                    value={localFilters.resource_types || []}
                    onChange={(e) =>
                      handleFilterChange('resource_types', e.target.value)
                    }
                    input={<OutlinedInput label="Resource Types" />}
                    renderValue={(selected) => (
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {(selected as ResourceType[]).map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {resourceTypes?.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        <Checkbox
                          checked={(localFilters.resource_types || []).indexOf(option.value as ResourceType) > -1}
                        />
                        <ListItemText primary={option.name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </FilterSection>

          {/* User & IP Filters */}
          <FilterSection
            title="User & Network"
            icon={<Person fontSize="small" />}
            section="user"
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="User ID"
                  size="small"
                  fullWidth
                  value={localFilters.user_id || ''}
                  onChange={(e) => handleFilterChange('user_id', e.target.value)}
                  InputProps={{
                    startAdornment: <Person fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                    endAdornment: localFilters.user_id && (
                      <IconButton
                        size="small"
                        onClick={() => handleClearFilter('user_id')}
                      >
                        <Clear fontSize="small" />
                      </IconButton>
                    ),
                  }}
                  placeholder="Enter user ID to filter"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="IP Address"
                  size="small"
                  fullWidth
                  value={localFilters.ip_address || ''}
                  onChange={(e) => handleFilterChange('ip_address', e.target.value)}
                  InputProps={{
                    startAdornment: <Computer fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                    endAdornment: localFilters.ip_address && (
                      <IconButton
                        size="small"
                        onClick={() => handleClearFilter('ip_address')}
                      >
                        <Clear fontSize="small" />
                      </IconButton>
                    ),
                  }}
                  placeholder="Enter IP address"
                />
              </Grid>
            </Grid>
          </FilterSection>

          {/* Severity & Compliance Filters */}
          <FilterSection
            title="Severity & Compliance"
            icon={<Business fontSize="small" />}
            section="compliance"
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Severity Level</InputLabel>
                  <Select
                    value={localFilters.severity || ''}
                    onChange={(e) =>
                      handleFilterChange('severity', e.target.value || undefined)
                    }
                    label="Severity Level"
                  >
                    <MenuItem value="">
                      <em>All Severities</em>
                    </MenuItem>
                    {SeverityOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Compliance Tags</InputLabel>
                  <Select
                    multiple
                    value={localFilters.compliance_tags || []}
                    onChange={(e) =>
                      handleFilterChange('compliance_tags', e.target.value)
                    }
                    input={<OutlinedInput label="Compliance Tags" />}
                    renderValue={(selected) => (
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {(selected as ComplianceTag[]).map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {complianceTags?.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        <Checkbox
                          checked={(localFilters.compliance_tags || []).indexOf(option.value as ComplianceTag) > -1}
                        />
                        <ListItemText primary={option.name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </FilterSection>

          {/* Organization Filter */}
          <FilterSection
            title="Organization"
            icon={<Business fontSize="small" />}
            section="organization"
          >
            <TextField
              label="Organization ID"
              size="small"
              fullWidth
              value={localFilters.organization_id || ''}
              onChange={(e) => handleFilterChange('organization_id', e.target.value)}
              InputProps={{
                startAdornment: <Business fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: localFilters.organization_id && (
                  <IconButton
                    size="small"
                    onClick={() => handleClearFilter('organization_id')}
                  >
                    <Clear fontSize="small" />
                  </IconButton>
                ),
              }}
              placeholder="Enter organization ID"
            />
          </FilterSection>
        </CardContent>

        {/* Filter Actions */}
        {!compact && (
          <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
            <Button
              variant="outlined"
              onClick={handleReset}
              startIcon={<Refresh />}
              disabled={isLoading}
            >
              Reset
            </Button>
            <Button
              variant="contained"
              onClick={handleApply}
              disabled={isLoading}
              startIcon={<FilterList />}
            >
              Apply Filters
            </Button>
          </CardActions>
        )}

        {/* Active Filters Summary */}
        {activeFilterCount > 0 && (
          <Box sx={{ p: 2, pt: 0 }}>
            <Typography variant="body2" color="text.secondary" mb={1}>
              Active Filters:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {localFilters.start_date && (
                <Chip
                  label={`From: ${format(new Date(localFilters.start_date), 'MMM dd, yyyy')}`}
                  size="small"
                  onDelete={() => handleClearFilter('start_date')}
                />
              )}
              {localFilters.end_date && (
                <Chip
                  label={`To: ${format(new Date(localFilters.end_date), 'MMM dd, yyyy')}`}
                  size="small"
                  onDelete={() => handleClearFilter('end_date')}
                />
              )}
              {localFilters.action_types?.map((type) => (
                <Chip
                  key={type}
                  label={`Action: ${type}`}
                  size="small"
                  onDelete={() => {
                    const newTypes = localFilters.action_types?.filter(t => t !== type);
                    handleFilterChange('action_types', newTypes?.length ? newTypes : undefined);
                  }}
                />
              ))}
              {localFilters.severity && (
                <Chip
                  label={`Severity: ${localFilters.severity}`}
                  size="small"
                  onDelete={() => handleClearFilter('severity')}
                />
              )}
              {localFilters.user_id && (
                <Chip
                  label={`User: ${localFilters.user_id}`}
                  size="small"
                  onDelete={() => handleClearFilter('user_id')}
                />
              )}
              {localFilters.ip_address && (
                <Chip
                  label={`IP: ${localFilters.ip_address}`}
                  size="small"
                  onDelete={() => handleClearFilter('ip_address')}
                />
              )}
            </Stack>
          </Box>
        )}
      </Card>
    </LocalizationProvider>
  );
};

export default AuditFilters;