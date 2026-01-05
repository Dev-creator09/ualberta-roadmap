"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

interface WarningsPanelProps {
  warnings: string[];
}

export function WarningsPanel({ warnings }: WarningsPanelProps) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <Alert variant="destructive" className="mb-8">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Roadmap Warnings</AlertTitle>
      <AlertDescription>
        <ul className="mt-2 space-y-1 list-disc list-inside">
          {warnings.map((warning, index) => (
            <li key={index} className="text-sm">
              {warning}
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
