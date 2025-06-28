import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  CircularProgress,
  Alert,
  IconButton,
  Typography,
  Chip,
  Paper,
  Stack,
  Divider
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  PictureAsPdf as PdfIcon,
  Print as PrintIcon,
  Share as ShareIcon
} from '@mui/icons-material';
import { pdfService, PDFResult } from '../services/pdfService';

interface PDFViewerProps {
  open: boolean;
  onClose: () => void;
  pdfData?: PDFResult;
  title?: string;
  patientName?: string;
}

const PDFViewer: React.FC<PDFViewerProps> = ({
  open,
  onClose,
  pdfData,
  title = 'Assessment Report',
  patientName
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfBlob, setPdfBlob] = useState<Blob | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    if (open && pdfData?.pdfUrl) {
      loadPDF();
    }
    
    return () => {
      // Cleanup blob URL
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [open, pdfData]);

  const loadPDF = async () => {
    if (!pdfData?.pdfUrl) return;

    setLoading(true);
    setError(null);

    try {
      // Verify PDF exists
      const isValid = await pdfService.verifyPDF(pdfData.pdfUrl);
      if (!isValid) {
        throw new Error('PDF file is not accessible');
      }

      // Get PDF blob for display
      const blob = await pdfService.getPDFBlob(pdfData.pdfUrl);
      if (blob) {
        setPdfBlob(blob);
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
      } else {
        throw new Error('Failed to load PDF content');
      }
    } catch (err) {
      console.error('Failed to load PDF:', err);
      setError(err instanceof Error ? err.message : 'Failed to load PDF');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!pdfData?.pdfUrl || !pdfData.filename) return;

    try {
      const success = await pdfService.downloadPDF(pdfData.pdfUrl, pdfData.filename);
      if (!success) {
        setError('Failed to download PDF');
      }
    } catch (err) {
      console.error('Download failed:', err);
      setError('Failed to download PDF');
    }
  };

  const handleOpenInNewTab = () => {
    if (pdfData?.pdfUrl) {
      pdfService.previewPDF(pdfData.pdfUrl);
    }
  };

  const handlePrint = () => {
    if (pdfUrl) {
      const printWindow = window.open(pdfUrl);
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print();
        };
      }
    }
  };

  const formatFileSize = (size?: number) => {
    if (!size) return 'Unknown size';
    return pdfService.formatFileSize(size);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PdfIcon color="error" />
            <Box>
              <Typography variant="h6">{title}</Typography>
              {patientName && (
                <Typography variant="body2" color="text.secondary">
                  Patient: {patientName}
                </Typography>
              )}
            </Box>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
        {/* PDF Metadata */}
        {pdfData?.metadata && (
          <Paper sx={{ m: 2, p: 2, backgroundColor: 'background.default' }}>
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Chip
                label={pdfData.metadata.assessmentType.toUpperCase()}
                color="primary"
                size="small"
              />
              <Typography variant="body2" color="text.secondary">
                Generated: {formatDate(pdfData.metadata.generatedAt)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Size: {formatFileSize(pdfData.metadata.size)}
              </Typography>
              {pdfData.filename && (
                <Typography variant="body2" color="text.secondary">
                  File: {pdfData.filename}
                </Typography>
              )}
            </Stack>
          </Paper>
        )}

        <Divider />

        {/* PDF Content */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
          {loading && (
            <Box sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              flexDirection: 'column',
              gap: 2
            }}>
              <CircularProgress />
              <Typography variant="body2" color="text.secondary">
                Loading PDF...
              </Typography>
            </Box>
          )}

          {error && (
            <Box sx={{ p: 2 }}>
              <Alert severity="error" action={
                <Button color="inherit" size="small" onClick={loadPDF}>
                  Retry
                </Button>
              }>
                {error}
              </Alert>
            </Box>
          )}

          {!loading && !error && pdfUrl && (
            <Box sx={{ flex: 1, width: '100%', height: '100%' }}>
              <iframe
                src={pdfUrl}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none'
                }}
                title="PDF Assessment Report"
              />
            </Box>
          )}

          {!loading && !error && !pdfUrl && pdfData && (
            <Box sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              flexDirection: 'column',
              gap: 2,
              p: 4
            }}>
              <PdfIcon sx={{ fontSize: 64, color: 'text.secondary' }} />
              <Typography variant="h6" color="text.secondary">
                PDF Preview Not Available
              </Typography>
              <Typography variant="body2" color="text.secondary" textAlign="center">
                The PDF cannot be displayed inline. Use the download or open buttons below to view the file.
              </Typography>
            </Box>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
          disabled={!pdfData?.pdfUrl}
          variant="outlined"
        >
          Download
        </Button>
        
        <Button
          startIcon={<VisibilityIcon />}
          onClick={handleOpenInNewTab}
          disabled={!pdfData?.pdfUrl}
          variant="outlined"
        >
          Open in New Tab
        </Button>

        <Button
          startIcon={<PrintIcon />}
          onClick={handlePrint}
          disabled={!pdfUrl}
          variant="outlined"
        >
          Print
        </Button>

        <Box sx={{ flex: 1 }} />

        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PDFViewer; 