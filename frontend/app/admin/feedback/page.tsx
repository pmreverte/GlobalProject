"use client";

import { useEffect, useState } from "react";
import axios from "axios";

interface Feedback {
  usuario: string;
  pregunta: string;
  fue_util: boolean;
  fecha: string;
}

export default function FeedbackAdmin() {
  const [datos, setDatos] = useState<Feedback[]>([]);
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        const res = await axios.get("http://localhost:8000/admin/feedback", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setDatos(res.data as Feedback[]);
      } catch {
        setError("No se pudieron cargar los feedbacks.");
      }
    };
    fetchFeedback();
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Feedback de Respuestas</h1>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <ul className="space-y-4">
        {datos.map((item, i) => (
          <li key={i} className="bg-white rounded-xl shadow p-4">
            <div className="text-sm text-gray-500">{item.fecha} - <strong>{item.usuario}</strong></div>
            <div className="mt-2"><strong>Pregunta:</strong> {item.pregunta}</div>
            <div className="mt-2">
              <strong>Feedback:</strong> {item.fue_util ? "✅ Útil" : "❌ No útil"}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
