import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { DatePicker } from '@/components/ui/date-picker';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { triggerIngestion, checkIngestionStatus } from '@/services/api';
import { IngestionJob } from '@/types';

export default function IngestionPage() {
  const [source, setSource] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Query active ingestion jobs
  const { data: activeJobs, isLoading } = useQuery<IngestionJob[]>(
    ['ingestion-jobs'],
    async () => {
      // Fetch active jobs from the API
      return [];
    },
    {
      refetchInterval: 5000, // Refetch every 5 seconds
    }
  );

  // Mutation for triggering ingestion
  const triggerIngestionMutation = useMutation(
    (params: {
      source: 'federal_register' | 'far_dfars' | 'standards';
      startDate?: string;
      endDate?: string;
      documentType?: string;
    }) => triggerIngestion(params),
    {
      onSuccess: () => {
        toast({
          title: 'Ingestion started',
          description: 'The ingestion job has been queued successfully.',
        });
        queryClient.invalidateQueries(['ingestion-jobs']);
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: 'Failed to start ingestion job. Please try again.',
          variant: 'destructive',
        });
      },
    }
  );

  const handleStartIngestion = () => {
    if (!source) {
      toast({
        title: 'Error',
        description: 'Please select a data source.',
        variant: 'destructive',
      });
      return;
    }

    triggerIngestionMutation.mutate({
      source: source as 'federal_register' | 'far_dfars' | 'standards',
      startDate: startDate?.toISOString().split('T')[0],
      endDate: endDate?.toISOString().split('T')[0],
      documentType: documentType || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Ingestion</h1>
        <p className="text-muted-foreground">
          Manage data ingestion from various sources
        </p>
      </div>

      {/* Ingestion form */}
      <Card>
        <CardHeader>
          <CardTitle>Start New Ingestion</CardTitle>
          <CardDescription>
            Configure and start a new data ingestion job
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="federal_register">Federal Register</SelectItem>
                <SelectItem value="far_dfars">FAR/DFARS</SelectItem>
                <SelectItem value="standards">Standards</SelectItem>
              </SelectContent>
            </Select>

            <Select value={documentType} onValueChange={setDocumentType}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Document type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rule">Rule</SelectItem>
                <SelectItem value="notice">Notice</SelectItem>
                <SelectItem value="standard">Standard</SelectItem>
              </SelectContent>
            </Select>

            <DatePicker
              selected={startDate}
              onChange={setStartDate}
              placeholderText="Start date"
              className="w-[200px]"
            />

            <DatePicker
              selected={endDate}
              onChange={setEndDate}
              placeholderText="End date"
              className="w-[200px]"
            />

            <Button
              onClick={handleStartIngestion}
              disabled={!source || triggerIngestionMutation.isLoading}
            >
              Start Ingestion
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Active jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Active Jobs</CardTitle>
          <CardDescription>
            Monitor currently running ingestion jobs
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-4">Loading jobs...</div>
          ) : activeJobs?.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              No active ingestion jobs
            </div>
          ) : (
            <div className="space-y-4">
              {activeJobs?.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{job.source}</div>
                    <div className="text-sm text-muted-foreground">
                      Started: {new Date(job.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-[200px]">
                      <Progress value={job.progress || 0} />
                    </div>
                    <div className="text-sm font-medium">
                      {job.progress ? `${job.progress}%` : job.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 