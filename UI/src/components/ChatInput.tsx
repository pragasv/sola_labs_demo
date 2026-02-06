import { useState, useRef, KeyboardEvent } from "react";
import { Send, Paperclip, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSubmit: (message: string, file?: File | null) => void;
  isLoading?: boolean;
  attachedFile: File | null;
  onFileAttach: (file: File | null) => void;
}

export function ChatInput({ onSubmit, isLoading, attachedFile, onFileAttach }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (message.trim() || attachedFile) {
      onSubmit(message.trim(), attachedFile);
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileAttach(file);
    }
  };

  return (
    <div className="relative">
      {attachedFile && (
        <div className="mb-3 flex items-center gap-2 rounded-lg bg-secondary/80 px-3 py-2 animate-fade-in">
          <Paperclip className="h-4 w-4 text-primary" />
          <span className="text-sm truncate flex-1">{attachedFile.name}</span>
          <button
            onClick={() => onFileAttach(null)}
            className="text-muted-foreground hover:text-destructive transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="flex items-end gap-3 rounded-2xl border border-border bg-card p-2 shadow-soft transition-shadow focus-within:shadow-elevated">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.doc,.docx,.txt,.md"
        />
        
        <Button
          variant="icon"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          className="shrink-0"
          disabled={isLoading}
        >
          <Paperclip className="h-5 w-5" />
        </Button>

        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your health documents..."
          className={cn(
            "min-h-[44px] max-h-[200px] flex-1 resize-none border-0 bg-transparent p-2 text-sm placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0"
          )}
          rows={1}
          disabled={isLoading}
        />

        <Button
          variant="gradient"
          size="icon"
          onClick={handleSubmit}
          disabled={isLoading || (!message.trim() && !attachedFile)}
          className="shrink-0"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>

      <p className="mt-2 text-center text-xs text-muted-foreground">
        Press Enter to send, Shift + Enter for new line
      </p>
    </div>
  );
}
