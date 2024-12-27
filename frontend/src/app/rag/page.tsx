'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { ragApi, type QueryResponse } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function RAGPage() {
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState('synthesis');

  const queryMutation = useMutation({
    mutationFn: ragApi.query,
    onError: (error) => {
      console.error('Error querying RAG:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      queryMutation.mutate({ query });
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Document Query Interface</h1>

      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-4">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query..."
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!query.trim() || queryMutation.isPending}
          >
            {queryMutation.isPending ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </form>

      {queryMutation.isError && (
        <Alert variant="destructive" className="mb-8">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            An error occurred while processing your query. Please try again.
          </AlertDescription>
        </Alert>
      )}

      {queryMutation.isPending && (
        <div className="space-y-4">
          <Skeleton className="h-[200px] w-full" />
          <Skeleton className="h-[100px] w-full" />
          <Skeleton className="h-[100px] w-full" />
        </div>
      )}

      {queryMutation.isSuccess && queryMutation.data && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="synthesis">Synthesis</TabsTrigger>
            <TabsTrigger value="sources">Sources</TabsTrigger>
          </TabsList>

          <TabsContent value="synthesis">
            <Card className="p-6">
              <h2 className="text-2xl font-semibold mb-4">Summary</h2>
              <p className="mb-6 text-muted-foreground">
                {queryMutation.data.synthesis.synthesis}
              </p>

              <h3 className="text-xl font-semibold mb-3">Key Points</h3>
              <ul className="list-disc pl-6 mb-6">
                {queryMutation.data.synthesis.key_points.map((point, index) => (
                  <li key={index} className="mb-2">
                    {point}
                  </li>
                ))}
              </ul>

              <h3 className="text-xl font-semibold mb-3">References</h3>
              <ul className="list-disc pl-6">
                {queryMutation.data.synthesis.references.map((ref, index) => (
                  <li key={index} className="mb-2">
                    {ref}
                  </li>
                ))}
              </ul>
            </Card>
          </TabsContent>

          <TabsContent value="sources">
            <div className="space-y-4">
              {queryMutation.data.sources.map((source) => (
                <Card key={source.id} className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-semibold">{source.title}</h3>
                    <div className="text-sm text-muted-foreground">
                      Score: {source.score.toFixed(2)}
                    </div>
                  </div>
                  <p className="mb-4 text-muted-foreground">{source.content}</p>
                  <div className="text-sm text-muted-foreground">
                    Source: {source.source} | ID: {source.id}
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
} 