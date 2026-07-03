/** Export actions for downloading generated test ZIP archive. */

import { Download, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

interface ExportActionsProps {
  downloadUrl: string;
}

export function ExportActions({ downloadUrl }: ExportActionsProps) {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      // Trigger direct download via the backend URL
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = "";
      a.click();
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleDownload}
      disabled={downloading}
    >
      {downloading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Downloading...
        </>
      ) : (
        <>
          <Download className="mr-2 h-4 w-4" />
          Download ZIP
        </>
      )}
    </Button>
  );
}
