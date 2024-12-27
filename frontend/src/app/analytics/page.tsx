import React from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { DatePicker } from '@/components/ui/date-picker';
import { BarChart, LineChart, PieChart } from '@/components/charts';

interface DocumentStats {
  total_documents: number;
  documents_by_source: {
    source: string;
    count: number;
  }[];
  documents_by_type: {
    type: string;
    count: number;
  }[];
  documents_over_time: {
    date: string;
    count: number;
  }[];
  top_topics: {
    topic: string;
    count: number;
  }[];
  top_agencies: {
    agency: string;
    count: number;
  }[];
}

export default function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery<DocumentStats>(
    ['document-stats'],
    async () => {
      // Fetch document statistics from the API
      return {
        total_documents: 1234,
        documents_by_source: [
          { source: 'Federal Register', count: 500 },
          { source: 'FAR/DFARS', count: 300 },
          { source: 'NIST', count: 250 },
          { source: 'ISO', count: 184 },
        ],
        documents_by_type: [
          { type: 'Rule', count: 400 },
          { type: 'Notice', count: 600 },
          { type: 'Standard', count: 234 },
        ],
        documents_over_time: Array.from({ length: 12 }, (_, i) => ({
          date: `2023-${(i + 1).toString().padStart(2, '0')}-01`,
          count: Math.floor(Math.random() * 100) + 50,
        })),
        top_topics: [
          { topic: 'Cybersecurity', count: 150 },
          { topic: 'Privacy', count: 120 },
          { topic: 'Compliance', count: 100 },
          { topic: 'Risk Management', count: 80 },
          { topic: 'Data Protection', count: 60 },
        ],
        top_agencies: [
          { agency: 'Department of Defense', count: 200 },
          { agency: 'GSA', count: 150 },
          { agency: 'NASA', count: 100 },
          { agency: 'Department of Energy', count: 80 },
          { agency: 'Department of State', count: 60 },
        ],
      };
    }
  );

  if (isLoading) {
    return <div className="text-center py-8">Loading analytics...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Document statistics and insights
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_documents}</div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Documents by source */}
        <Card>
          <CardHeader>
            <CardTitle>Documents by Source</CardTitle>
          </CardHeader>
          <CardContent>
            <PieChart
              data={stats?.documents_by_source.map(item => ({
                name: item.source,
                value: item.count,
              })) || []}
            />
          </CardContent>
        </Card>

        {/* Documents by type */}
        <Card>
          <CardHeader>
            <CardTitle>Documents by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart
              data={stats?.documents_by_type.map(item => ({
                name: item.type,
                value: item.count,
              })) || []}
            />
          </CardContent>
        </Card>

        {/* Documents over time */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Documents Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart
              data={stats?.documents_over_time.map(item => ({
                date: item.date,
                value: item.count,
              })) || []}
            />
          </CardContent>
        </Card>

        {/* Top topics */}
        <Card>
          <CardHeader>
            <CardTitle>Top Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart
              data={stats?.top_topics.map(item => ({
                name: item.topic,
                value: item.count,
              })) || []}
            />
          </CardContent>
        </Card>

        {/* Top agencies */}
        <Card>
          <CardHeader>
            <CardTitle>Top Agencies</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart
              data={stats?.top_agencies.map(item => ({
                name: item.agency,
                value: item.count,
              })) || []}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 