import "@/styles/globals.css";
import { ReactNode } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agente IA Multifuente",
  description: "Agente IA Multifuente",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </body>
    </html>
  );
}