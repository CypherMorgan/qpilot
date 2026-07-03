import { useNavigate } from "react-router-dom";
import { FileQuestion, ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 p-8 text-center">
      <FileQuestion className="h-16 w-16 text-muted-foreground" />
      <div>
        <h1 className="text-4xl font-bold tracking-tight">404</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          This page doesn&apos;t exist.
        </p>
      </div>
      <Button variant="outline" onClick={() => navigate("/")}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Button>
    </div>
  );
}
