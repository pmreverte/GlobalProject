"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

interface Analytics {
  totalQueries: number;
  averageResponseTime: number;
  userStats: {
    username: string;
    queryCount: number;
  }[];
  feedbackStats: {
    positive: number;
    negative: number;
    neutral: number;
  };
  queryCountByDate: {
    date: string;
    count: number;
  }[];
  topTopics: {
    topic: string;
    count: number;
  }[];
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [timeRange, setTimeRange] = useState("week"); // week, month, year
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("No autorizado");

      const response = await fetch(`/api/admin/analytics?range=${timeRange}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.error("Error response:", await response.text());
        throw new Error(`Error al cargar analíticas: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Analytics data:", data);
      setAnalytics(data);
      setLoading(false);
    } catch (error) {
      setError("Error al cargar analíticas");
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Cargando analíticas...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Analíticas del Sistema</h1>
        <div className="space-x-2">
          <Button
            onClick={() => setTimeRange("week")}
            className={timeRange === "week" ? "bg-blue-700" : ""}
          >
            Semana
          </Button>
          <Button
            onClick={() => setTimeRange("month")}
            className={timeRange === "month" ? "bg-blue-700" : ""}
          >
            Mes
          </Button>
          <Button
            onClick={() => setTimeRange("year")}
            className={timeRange === "year" ? "bg-blue-700" : ""}
          >
            Año
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Métricas Generales */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Métricas Generales</h2>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600">Total de Consultas</p>
              <p className="text-3xl font-bold">{analytics.totalQueries}</p>
            </div>
            <div>
              <p className="text-gray-600">Tiempo Promedio de Respuesta</p>
              <p className="text-3xl font-bold">{analytics.averageResponseTime.toFixed(2)}s</p>
            </div>
          </div>
        </div>

        {/* Estadísticas de Feedback */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Feedback</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Positivo</span>
              <span className="text-green-600 font-bold">{analytics.feedbackStats.positive}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Neutral</span>
              <span className="text-yellow-600 font-bold">{analytics.feedbackStats.neutral}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Negativo</span>
              <span className="text-red-600 font-bold">{analytics.feedbackStats.negative}</span>
            </div>
          </div>
        </div>

        {/* Usuarios Más Activos */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Usuarios Más Activos</h2>
          <div className="space-y-2">
            {analytics.userStats.map((user, index) => (
              <div key={user.username} className="flex items-center justify-between">
                <span className="text-gray-600">{user.username}</span>
                <span className="font-bold">{user.queryCount} consultas</span>
              </div>
            ))}
          </div>
        </div>

        {/* Temas Más Consultados */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Temas Más Consultados</h2>
          <div className="space-y-2">
            {analytics.topTopics.map((topic, index) => (
              <div key={topic.topic} className="flex items-center justify-between">
                <span className="text-gray-600">{topic.topic}</span>
                <span className="font-bold">{topic.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Consultas por Fecha */}
        <div className="bg-white p-6 rounded-lg shadow-md col-span-2">
          <h2 className="text-xl font-semibold mb-4">Consultas por Fecha</h2>
          <div className="h-64">
            {/* Aquí se podría agregar un gráfico de líneas usando una librería como Chart.js */}
            <div className="space-y-2">
              {analytics.queryCountByDate.map((item) => (
                <div key={item.date} className="flex items-center justify-between">
                  <span className="text-gray-600">{new Date(item.date).toLocaleDateString()}</span>
                  <span className="font-bold">{item.count} consultas</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}