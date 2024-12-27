import React, { useState } from 'react';
import { DocumentList } from '@/components/DocumentList';
import { DocumentDetail } from '@/components/DocumentDetail';

export default function DocumentsPage() {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">
            Browse and search through regulatory documents
          </p>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Document list */}
        <div className={selectedDocumentId ? 'w-1/2' : 'w-full'}>
          <DocumentList
            onDocumentSelect={(documentId) => setSelectedDocumentId(documentId)}
          />
        </div>

        {/* Document detail */}
        {selectedDocumentId && (
          <div className="w-1/2">
            <DocumentDetail
              documentId={selectedDocumentId}
            />
          </div>
        )}
      </div>
    </div>
  );
} 