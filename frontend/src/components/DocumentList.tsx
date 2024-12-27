import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { DatePicker } from '@/components/ui/date-picker';
import { Pagination } from '@/components/ui/pagination';
import { fetchDocuments } from '@/services/api';
import { Document } from '@/types';

interface DocumentListProps {
  onDocumentSelect: (documentId: string) => void;
}

export function DocumentList({ onDocumentSelect }: DocumentListProps) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [source, setSource] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);

  const { data, isLoading, error } = useQuery(
    ['documents', page, pageSize, source, documentType, startDate, endDate],
    () => fetchDocuments({
      page,
      pageSize,
      source,
      documentType,
      startDate: startDate?.toISOString().split('T')[0],
      endDate: endDate?.toISOString().split('T')[0],
    })
  );

  const handleRowClick = (documentId: string) => {
    onDocumentSelect(documentId);
  };

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading documents...</div>;
  }

  if (error) {
    return (
      <div className="flex justify-center p-8 text-red-500">
        Error loading documents: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 p-4 bg-white rounded-lg shadow">
        <Select value={source} onValueChange={setSource}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="federal_register">Federal Register</SelectItem>
            <SelectItem value="far_dfars">FAR/DFARS</SelectItem>
            <SelectItem value="nist">NIST</SelectItem>
            <SelectItem value="iso">ISO</SelectItem>
          </SelectContent>
        </Select>

        <Select value={documentType} onValueChange={setDocumentType}>
          <SelectTrigger className="w-[180px]">
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
          className="w-[180px]"
        />

        <DatePicker
          selected={endDate}
          onChange={setEndDate}
          placeholderText="End date"
          className="w-[180px]"
        />

        <Button
          variant="outline"
          onClick={() => {
            setSource(null);
            setDocumentType(null);
            setStartDate(null);
            setEndDate(null);
          }}
        >
          Clear filters
        </Button>
      </div>

      {/* Documents table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Document ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Publication Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.documents.map((doc: Document) => (
              <TableRow
                key={doc.document_id}
                onClick={() => handleRowClick(doc.document_id)}
                className="cursor-pointer hover:bg-gray-50"
              >
                <TableCell>{doc.document_id}</TableCell>
                <TableCell>{doc.title}</TableCell>
                <TableCell>{doc.source}</TableCell>
                <TableCell>{doc.document_type}</TableCell>
                <TableCell>{doc.publication_date}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, data?.total || 0)} of {data?.total || 0} documents
          </span>
          <Select
            value={pageSize.toString()}
            onValueChange={(value) => setPageSize(parseInt(value))}
          >
            <SelectTrigger className="w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10 / page</SelectItem>
              <SelectItem value="25">25 / page</SelectItem>
              <SelectItem value="50">50 / page</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Pagination
          currentPage={page}
          totalPages={Math.ceil((data?.total || 0) / pageSize)}
          onPageChange={setPage}
        />
      </div>
    </div>
  );
} 