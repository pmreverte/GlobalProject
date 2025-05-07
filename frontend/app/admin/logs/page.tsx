"use client";

import LogViewer from "@/components/LogViewer";

export default function LogsPage() {
  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-6">Logs del Sistema</h1>
      <LogViewer />
    </div>
  );
}