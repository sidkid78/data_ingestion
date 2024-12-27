import { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/toaster';
import { cn } from '@/lib/utils';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Document Management System',
  description: 'A system for managing and analyzing regulatory documents',
  viewport: 'width=device-width, initial-scale=1',
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className={cn(
        'min-h-screen bg-background font-sans antialiased',
        inter.className
      )}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <div className="relative flex min-h-screen flex-col">
              <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container flex h-14 items-center">
                  <div className="mr-4 flex">
                    <a href="/" className="mr-6 flex items-center space-x-2">
                      <span className="font-bold">DMS</span>
                    </a>
                  </div>
                  <nav className="flex items-center space-x-6 text-sm font-medium">
                    <a
                      href="/documents"
                      className="transition-colors hover:text-foreground/80"
                    >
                      Documents
                    </a>
                    <a
                      href="/ingestion"
                      className="transition-colors hover:text-foreground/80"
                    >
                      Ingestion
                    </a>
                    <a
                      href="/analytics"
                      className="transition-colors hover:text-foreground/80"
                    >
                      Analytics
                    </a>
                  </nav>
                </div>
              </header>
              <main className="flex-1">
                <div className="container py-6">
                  {children}
                </div>
              </main>
              <footer className="border-t py-6">
                <div className="container flex flex-col items-center justify-between gap-4 md:h-14 md:flex-row">
                  <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                    Built with Next.js, Tailwind CSS, and Shadcn UI.
                  </p>
                </div>
              </footer>
            </div>
            <Toaster />
          </ThemeProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
} 