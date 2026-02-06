import { FileQuestion, Upload, MessageCircle } from "lucide-react";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center animate-fade-in">
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl gradient-primary shadow-glow mb-6">
        <FileQuestion className="h-10 w-10 text-primary-foreground" />
      </div>
      
      <h2 className="text-xl font-semibold text-foreground mb-2">
        Welcome to HealthAI Assistant
      </h2>
      <p className="text-muted-foreground max-w-md mb-8">
        Upload a medical document or ask any health-related question to get started.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 max-w-lg w-full">
        <div className="flex items-start gap-3 rounded-xl bg-card border border-border p-4 text-left">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            <Upload className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-sm">Upload Documents</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Attach PDF, DOC, or TXT files for analysis
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-xl bg-card border border-border p-4 text-left">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10">
            <MessageCircle className="h-5 w-5 text-accent" />
          </div>
          <div>
            <p className="font-medium text-sm">Ask Questions</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Get instant answers from your documents
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
