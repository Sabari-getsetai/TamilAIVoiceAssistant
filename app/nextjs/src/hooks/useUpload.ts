import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AdminApiService, validateFiles, handleApiError } from '../services/api/adminApi';

interface UploadFileItem {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

export const useUpload = () => {
  const [files, setFiles] = useState<UploadFileItem[]>([]);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: AdminApiService.uploadDocuments,
    onSuccess: async (response) => {
      // Extract file paths from upload response
      const filePaths = response.files.map((file) => file.path);

      // Trigger ingestion with file paths
      await AdminApiService.triggerIngestion(filePaths);

      // Update files to completed status
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: 'completed' as const }))
      );

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });

      // Clear files after a delay
      setTimeout(() => {
        setFiles([]);
      }, 2000);
    },
    onError: (error) => {
      const errorMessage = handleApiError(error);
      
      // Update files to error status
      setFiles((prev) =>
        prev.map((f) => ({
          ...f,
          status: 'error' as const,
          error: errorMessage,
        }))
      );
    },
  });

  const addFiles = (newFiles: File[]) => {
    const { valid, invalid } = validateFiles(newFiles);

    // Return validation errors for invalid files
    const validationErrors = invalid.map(({ file, reason }) => ({
      file: file.name,
      reason,
    }));

    // Add valid files to the list
    const fileItems: UploadFileItem[] = valid.map((file) => ({
      file,
      id: `${file.name}-${Date.now()}`,
      status: 'pending',
    }));

    setFiles((prev) => [...prev, ...fileItems]);

    return { validationErrors };
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      throw new Error('Please select files to upload');
    }

    // Update all files to uploading status
    setFiles((prev) =>
      prev.map((f) => ({ ...f, status: 'uploading' as const }))
    );

    // Upload files
    const filesToUpload = files.map((f) => f.file);
    return uploadMutation.mutateAsync(filesToUpload);
  };

  return {
    files,
    addFiles,
    removeFile,
    uploadFiles,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
  };
};
