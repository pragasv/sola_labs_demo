import { useState, useRef, useEffect } from "react";
import { Header } from "@/components/Header";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { EmptyState } from "@/components/EmptyState";
import { DocumentUpload } from "@/components/DocumentUpload";


interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [showUploadArea, setShowUploadArea] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (message: string, file?: File | null) => {
  if (!message && !file) return;

  const userMessage: Message = {
    id: Date.now().toString(),
    role: "user",
    content: file ? `[Attached: ${file.name}]\n\n${message}` : message,
  };

  setMessages((prev) => [...prev, userMessage]);
  setAttachedFile(null);
  setIsLoading(true);

  try {
    const formData = new FormData();
    formData.append("prompt_text", message);

    if (file) {
      formData.append("file", file);
    }

    const response = await fetch("/agent/process", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      console.error(`API error: ${response.status}`);
      throw new Error(`API error: ${response.status}`);

    }
    type AgentResponse = { answer: string };
    const data = (await response.json()) as AgentResponse;

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: data.answer,
    };

    setMessages((prev) => [...prev, assistantMessage]);

  } catch (error) {
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: error.message || "An error occurred while processing your request.",
    };

    setMessages((prev) => [...prev, assistantMessage]);
    console.error(error);
  } finally {
    setIsLoading(false);
  }
};

  const handleFileSelect = (file: File | null) => {
    setAttachedFile(file);
    if (file) {
      setShowUploadArea(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col gradient-soft">
      <Header />

      <main className="flex flex-1 flex-col">
        <div className="container mx-auto flex flex-1 flex-col px-4 py-6 max-w-4xl">
          {/* Upload Area Toggle */}
          {messages.length === 0 && !showUploadArea && (
            <EmptyState />
          )}

          {/* Document Upload Area */}
          {showUploadArea && messages.length === 0 && (
            <div className="mb-6 animate-fade-in">
              <DocumentUpload
                onFileSelect={handleFileSelect}
                selectedFile={attachedFile}
              />
            </div>
          )}

          {/* Messages */}
          {messages.length > 0 && (
            <div className="flex-1 space-y-6 pb-6">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                />
              ))}
              {isLoading && (
                <ChatMessage role="assistant" content="" isLoading />
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input Area */}
          <div className="sticky bottom-0 bg-gradient-to-t from-background via-background to-transparent pt-4 pb-4">
            <ChatInput
              onSubmit={handleSubmit}
              isLoading={isLoading}
              attachedFile={attachedFile}
              onFileAttach={setAttachedFile}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
