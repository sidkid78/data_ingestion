'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, LineChart, PieChart } from '@/components/charts';
import { getFederalRegisterStats } from '@/services/federal-register';

export default function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['federal-register-stats'],
    queryFn: getFederalRegisterStats,
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Documents by Type</CardTitle>
          </CardHeader>
          <CardContent>
            {stats && (
              <PieChart
                data={stats.documents_by_type.map(item => ({
                  name: item.type,
                  value: item.count,
                }))}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Agencies</CardTitle>
          </CardHeader>
          <CardContent>
            {stats && (
              <BarChart
                data={stats.documents_by_agency.map(item => ({
                  name: item.agency,
                  value: item.count,
                }))}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Documents Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            {stats && (
              <LineChart
                data={stats.documents_over_time.map(item => ({
                  date: item.date,
                  value: item.count,
                }))}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 