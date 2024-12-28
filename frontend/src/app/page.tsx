export default function HomePage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4">
        <h1 className="text-4xl font-bold">Document Management System</h1>
        <p className="text-xl text-muted-foreground">
          Manage, analyze, and process regulatory documents efficiently.
        </p>
      </section>

      <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border p-4">
          <h2 className="text-lg font-semibold">Document Management</h2>
          <p className="text-muted-foreground">
            Upload, organize, and manage your regulatory documents.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h2 className="text-lg font-semibold">Data Ingestion</h2>
          <p className="text-muted-foreground">
            Automated ingestion from Federal Register, FAR/DFARS, and standards.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h2 className="text-lg font-semibold">Analytics</h2>
          <p className="text-muted-foreground">
            Analyze relationships and compliance across your documents.
          </p>
        </div>
      </section>
    </div>
  );
} 