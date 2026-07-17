/** File upload component — drag & drop or click to attach artifact files.

Supports text files (JSON, HTML, logs, etc.) and common image formats.
Files are displayed in a list with type icons and a remove button.
*/

import { useCallback, useRef, useState } from "react";
import { FileImage, FileText, File, X, Upload, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = [
  ".json", ".txt", ".md", ".html", ".htm", ".xml", ".yaml", ".yml",
  ".csv", ".log", ".env", ".cfg", ".ini", ".conf", ".toml",
  ".py", ".js", ".ts", ".jsx", ".tsx",
  ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

export interface FileEntry {
  id: string;
  file: File;
  preview: string | null; // base64 data URL or null for text files
  error?: string;
}

interface FileUploadProps {
  files: FileEntry[];
  onFilesChange: (files: FileEntry[]) => void;
  disabled?: boolean;
}

function getFileIcon(filename: string): React.ReactNode {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  const imageExts = ["png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"];
  const textExts = [
    "json", "txt", "md", "html", "htm", "xml", "yaml", "yml",
    "csv", "log", "py", "js", "ts", "jsx", "tsx",
  ];
  if (imageExts.includes(ext)) return <FileImage className="h-4 w-4 text-blue-500" />;
  if (textExts.includes(ext)) return <FileText className="h-4 w-4 text-amber-500" />;
  return <File className="h-4 w-4 text-muted-foreground" />;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUpload({ files, onFilesChange, disabled = false }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const addFiles = useCallback(
    async (incoming: FileList | File[]) => {
      const newEntries: FileEntry[] = [];
      for (const file of Array.from(incoming)) {
        if (file.size > MAX_FILE_SIZE) {
          newEntries.push({
            id: crypto.randomUUID(),
            file,
            preview: null,
            error: `File exceeds 10 MB limit (${formatSize(file.size)})`,
          });
          continue;
        }

        let preview: string | null = null;
        if (file.type.startsWith("image/")) {
          preview = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.readAsDataURL(file);
          });
        }

        newEntries.push({ id: crypto.randomUUID(), file, preview });
      }
      onFilesChange([...files, ...newEntries]);
    },
    [files, onFilesChange],
  );

  const removeFile = useCallback(
    (id: string) => {
      onFilesChange(files.filter((f) => f.id !== id));
    },
    [files, onFilesChange],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files);
      }
    },
    [addFiles],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          "relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/40",
          disabled && "pointer-events-none opacity-50",
        )}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            inputRef.current?.click();
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES.join(",")}
          className="hidden"
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = "";
          }}
          disabled={disabled}
        />
        <Upload className="mb-2 h-6 w-6 text-muted-foreground/60" />
        <p className="text-sm font-medium text-muted-foreground">
          Drop files here or click to browse
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground/50">
          JSON, HTML, logs, images &mdash; max 10 MB each
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="space-y-1.5">
          {files.map((entry) => (
            <li
              key={entry.id}
              className={cn(
                "flex items-center gap-3 rounded-lg border bg-card px-3 py-2 text-sm",
                entry.error && "border-destructive/40",
              )}
            >
              {entry.preview ? (
                <div className="h-8 w-8 shrink-0 overflow-hidden rounded border bg-muted">
                  <img
                    src={entry.preview}
                    alt={entry.file.name}
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border bg-muted">
                  {getFileIcon(entry.file.name)}
                </div>
              )}
              <div className="min-w-0 flex-1 truncate">
                <p className="truncate font-medium">{entry.file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatSize(entry.file.size)}
                </p>
              </div>
              {entry.error && (
                <div className="flex items-center gap-1 text-xs text-destructive" title={entry.error}>
                  <AlertCircle className="h-3 w-3" />
                </div>
              )}
              <button
                type="button"
                onClick={() => removeFile(entry.id)}
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground/50 hover:bg-destructive/10 hover:text-destructive"
                disabled={disabled}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {files.length > 0 && !disabled && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFilesChange([])}
          className="text-xs text-muted-foreground"
        >
          Clear all files
        </Button>
      )}
    </div>
  );
}
