"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // If user is already logged in, redirect to consultas
    const token = localStorage.getItem("token");
    if (token) {
      router.push("/consultas");
    }
  }, [router]);

  return (
    <div className="max-w-4xl mx-auto mt-20 px-4 text-center">
      <h1 className="text-4xl font-bold text-gray-800 mb-6">
        🤖 Bienvenido al Agente IA Multifuente
      </h1>
      
      <p className="text-xl text-gray-600 mb-8">
        Un asistente inteligente que combina datos estructurados y documentos 
        para responder tus preguntas de manera precisa y contextual.
      </p>

      <div className="space-x-4">
        <Button
          onClick={() => router.push("/login")}
          className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-3"
        >
          Iniciar Sesión
        </Button>
      </div>

      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-6 bg-white rounded-xl shadow-sm">
          <h3 className="text-xl font-semibold mb-3">🔍 Consulta SQL</h3>
          <p className="text-gray-600">
            Accede a datos estructurados de manera natural a través de consultas en lenguaje común.
          </p>
        </div>

        <div className="p-6 bg-white rounded-xl shadow-sm">
          <h3 className="text-xl font-semibold mb-3">📄 Análisis de Documentos</h3>
          <p className="text-gray-600">
            Obtén información relevante de documentos PDF y otros archivos de texto.
          </p>
        </div>

        <div className="p-6 bg-white rounded-xl shadow-sm">
          <h3 className="text-xl font-semibold mb-3">🧠 IA Avanzada</h3>
          <p className="text-gray-600">
            Respuestas generadas por modelos de lenguaje de última generación.
          </p>
        </div>
      </div>
    </div>
  );
}
