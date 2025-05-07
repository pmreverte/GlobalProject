"use client";

import { useState } from "react";
import api from "@/lib/api";

interface Props {
  pregunta: string;
  llmId?: number;
  feedback?: {
    fue_util: boolean;
  };
}

export function FeedbackRespuesta({ pregunta, llmId, feedback }: Props) {
  const [estado, setEstado] = useState<string | null>(null);

  const enviarFeedback = async (fue_util: boolean) => {
    try {
      if (!localStorage.getItem('token')) {
        setEstado("❌ Error: Debes iniciar sesión para enviar feedback.");
        return;
      }
      
      await api.post("/query/feedback", { pregunta, fue_util, llm_id: llmId });
      setEstado(fue_util ? "✅ Gracias por tu validación." : "❌ Lamentamos que no fuera útil.");
    } catch (error: any) {
      console.error("Error al registrar feedback:", error);
      
      if (error.response?.status === 401) {
        setEstado("❌ Error: Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.");
      } else if (error.response?.status === 403) {
        if (error.response.data?.detail === "Usuario no encontrado") {
          setEstado("❌ Error: Usuario no encontrado. Por favor, vuelve a iniciar sesión.");
        } else {
          setEstado("❌ Error: No tienes permisos para enviar feedback. Contacta con el administrador.");
        }
      } else if (error.response?.data?.detail) {
        setEstado(`❌ Error: ${error.response.data.detail}`);
      } else if (error.message === 'Network Error') {
        setEstado("❌ Error: No se pudo conectar con el servidor.");
      } else {
        setEstado("❌ Error al registrar el feedback. Por favor, inténtalo de nuevo.");
      }
    }
  };

  return (
    <div>
      {feedback ? (
        <span className="text-sm text-gray-600">
          {feedback.fue_util ? "✅ Esta respuesta fue marcada como útil" : "❌ Esta respuesta fue marcada como no útil"}
        </span>
      ) : !estado ? (
        <>
          <span className="text-sm text-gray-600 mr-2">¿Fue útil esta respuesta?</span>
          <button
            className="font-medium rounded-md transition-all duration-200 py-0.5 px-2.5 text-xs border border-blue-500 text-blue-600 hover:bg-blue-500 hover:text-white shadow-sm hover:shadow-md"
            onClick={() => enviarFeedback(true)}
          >
            Sí
          </button>
          <button
            className="font-medium rounded-md transition-all duration-200 py-0.5 px-2.5 text-xs border border-blue-500 text-blue-600 hover:bg-blue-500 hover:text-white shadow-sm hover:shadow-md ml-2"
            onClick={() => enviarFeedback(false)}
          >
            No
          </button>
        </>
      ) : (
        <span className="text-sm text-gray-600">{estado}</span>
      )}
    </div>
  );
}
