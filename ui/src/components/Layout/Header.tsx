import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Chip,
  Avatar,
  Badge,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  AccountCircle as AccountCircleIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store/store';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { selectedFramework, activeAgents } = useSelector((state: RootState) => state.agents);
  const { isConnected } = useSelector((state: RootState) => state.conversations);
  const { currentPatient } = useSelector((state: RootState) => state.patients);
  
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);
  const [profileAnchorEl, setProfileAnchorEl] = useState<null | HTMLElement>(null);

  const busyAgents = activeAgents.filter(agent => agent.status === 'busy').length;

  // Mock notifications data
  const notifications = [
    {
      id: 1,
      type: 'success',
      title: 'Patient Assessment Complete',
      message: 'Assessment for Patient ID 597173 has been completed successfully.',
      time: '5 minutes ago'
    },
    {
      id: 2,
      type: 'warning',
      title: 'FHIR Connection Warning',
      message: 'FHIR server response time is elevated. Consider checking connectivity.',
      time: '15 minutes ago'
    }
  ];

  const handleNotificationClick = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleSettingsClick = () => {
    navigate('/settings');
  };

  const handleProfileClick = (event: React.MouseEvent<HTMLElement>) => {
    setProfileAnchorEl(event.currentTarget);
  };

  const handleProfileClose = () => {
    setProfileAnchorEl(null);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
      default:
        return <InfoIcon color="info" />;
    }
  };

  return (
    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <PsychologyIcon sx={{ mr: 2 }} />
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Healthcare AI Agents
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Framework indicator */}
          <Chip
            label={selectedFramework.toUpperCase()}
            color={selectedFramework === 'autogen' ? 'primary' : 'secondary'}
            size="small"
            variant="outlined"
          />
          
          {/* Connection status */}
          <Chip
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            size="small"
            sx={{ color: 'white', borderColor: 'white' }}
          />
          
          {/* Current patient */}
          {currentPatient && (
            <Chip
              label={`Patient: ${currentPatient.name}`}
              color="info"
              size="small"
              sx={{ color: 'white', borderColor: 'white' }}
            />
          )}
          
          {/* Active agents indicator */}
          <Badge badgeContent={busyAgents} color="error">
            <Chip
              label={`${activeAgents.length} Agents`}
              size="small"
              sx={{ color: 'white', borderColor: 'white' }}
            />
          </Badge>
          
          {/* Notifications */}
          <IconButton 
            color="inherit" 
            onClick={handleNotificationClick}
            aria-label="notifications"
          >
            <Badge badgeContent={notifications.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          
          {/* Notifications Menu */}
          <Menu
            anchorEl={notificationAnchorEl}
            open={Boolean(notificationAnchorEl)}
            onClose={handleNotificationClose}
            PaperProps={{
              sx: { width: 350, maxHeight: 400 }
            }}
          >
            <MenuItem sx={{ fontWeight: 'bold', pointerEvents: 'none' }}>
              Notifications ({notifications.length})
            </MenuItem>
            <Divider />
            {notifications.map((notification) => (
              <MenuItem key={notification.id} onClick={handleNotificationClose}>
                <ListItemIcon>
                  {getNotificationIcon(notification.type)}
                </ListItemIcon>
                <ListItemText
                  primary={notification.title}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.disabled">
                        {notification.time}
                      </Typography>
                    </Box>
                  }
                />
              </MenuItem>
            ))}
            {notifications.length === 0 && (
              <MenuItem onClick={handleNotificationClose}>
                <ListItemText primary="No new notifications" />
              </MenuItem>
            )}
          </Menu>
          
          {/* Settings */}
          <IconButton 
            color="inherit" 
            onClick={handleSettingsClick}
            aria-label="settings"
          >
            <SettingsIcon />
          </IconButton>
          
          {/* User profile */}
          <IconButton 
            color="inherit" 
            onClick={handleProfileClick}
            aria-label="user profile"
          >
            <Avatar sx={{ width: 32, height: 32 }}>
              <AccountCircleIcon />
            </Avatar>
          </IconButton>
          
          {/* Profile Menu */}
          <Menu
            anchorEl={profileAnchorEl}
            open={Boolean(profileAnchorEl)}
            onClose={handleProfileClose}
            PaperProps={{
              sx: { width: 200 }
            }}
          >
            <MenuItem onClick={() => { handleProfileClose(); navigate('/settings'); }}>
              <ListItemIcon>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Settings" />
            </MenuItem>
            <MenuItem onClick={handleProfileClose}>
              <ListItemIcon>
                <AccountCircleIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Profile" />
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 