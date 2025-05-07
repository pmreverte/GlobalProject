"use client";

import ChatBox from "@/components/ChatBox";

export default function ConsultasPage() {
  return (
    <div className="max-w-3xl mx-auto mt-10 px-4 space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">💬 Consulta Inteligente</h1>
      <ChatBox />
    </div>
  );
}