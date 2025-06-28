import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  Box,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Person as PersonIcon,
  SmartToy as SmartToyIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Timeline as TimelineIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Patient Search', icon: <PersonIcon />, path: '/patients' },
  { text: 'Agent Console (Demo)', icon: <SmartToyIcon />, path: '/agents' },
  { text: 'Real Agent Console', icon: <PsychologyIcon />, path: '/real-agents' },
  { text: 'Conversation History', icon: <HistoryIcon />, path: '/conversations' },
  { text: 'Agent Communication History', icon: <TimelineIcon />, path: '/agent-communications' },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto' }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        
        <Divider />
        
        <List>
          <ListItem disablePadding>
            <ListItemButton onClick={() => navigate('/settings')}>
              <ListItemIcon>
                <SettingsIcon />
              </ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItemButton>
          </ListItem>
        </List>
        
        <Box sx={{ p: 2, mt: 'auto' }}>
          <Typography variant="caption" color="text.secondary">
            Healthcare AI Agents v1.0
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Sidebar; 