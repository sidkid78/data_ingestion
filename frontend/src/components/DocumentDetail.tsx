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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ForceGraph } from '@/components/ForceGraph';
import { fetchDocument, fetchDocumentRelationships } from '@/services/api';
import { Document, Relationship } from '@/types';

interface DocumentDetailProps {
  documentId: string;
}

export function DocumentDetail({ documentId }: DocumentDetailProps) {
  const { data: document, isLoading: isLoadingDoc, error: docError } = useQuery(
    ['document', documentId],
    () => fetchDocument(documentId)
  );

  const { data: relationships, isLoading: isLoadingRels, error: relsError } = useQuery(
    ['relationships', documentId],
    () => fetchDocumentRelationships(documentId)
  );

  if (isLoadingDoc || isLoadingRels) {
    return <div className="flex justify-center p-8">Loading document details...</div>;
  }

  if (docError || relsError) {
    return (
      <div className="flex justify-center p-8 text-red-500">
        Error loading document details: {(docError || relsError)?.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Document header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl">{document.title}</CardTitle>
              <CardDescription>Document ID: {document.document_id}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline">{document.source}</Badge>
              <Badge>{document.document_type}</Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Document content tabs */}
      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="relationships">Relationships</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
        </TabsList>

        <TabsContent value="details">
          <Card>
            <CardContent className="p-6">
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Publication Date</dt>
                  <dd className="mt-1">{document.publication_date}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                  <dd className="mt-1">{document.updated_at}</dd>
                </div>
                {Object.entries(document.metadata || {}).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-sm font-medium text-gray-500">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </dt>
                    <dd className="mt-1">
                      {typeof value === 'string' ? value : JSON.stringify(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="relationships">
          <Card>
            <CardContent className="p-6">
              <div className="h-[600px]">
                <ForceGraph
                  document={document}
                  relationships={relationships}
                  onNodeClick={(nodeId) => {
                    // Handle node click, e.g., navigate to related document
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="content">
          <Card>
            <CardContent className="p-6">
              <ScrollArea className="h-[600px] w-full">
                <div className="prose max-w-none">
                  {document.metadata?.content_summary || 'No content available'}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 