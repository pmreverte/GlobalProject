import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface QueryLog {
  tipo: 'consulta';
  usuario: string;
  pregunta: string;
  sql: string;
  respuesta: string;
  fecha: string;
}

interface AdminLog {
  tipo: 'admin';
  usuario: string;
  accion: string;
  modulo: string;
  detalles: any;
  fecha: string;
}

type Log = QueryLog | AdminLog;

export default function LogViewer() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await api.get('/api/admin/logs');
        setLogs(response.data);
      } catch (error: any) {
        console.error('Error fetching logs:', error);
        setError(error.response?.data?.error || error.message || 'Error al cargar los logs');
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  if (loading) {
    return <div className="p-4">Cargando logs...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">Error: {error}</div>;
  }

  if (!logs.length) {
    return <div className="p-4">No hay logs disponibles</div>;
  }

  const renderLogContent = (log: Log) => {
    if (log.tipo === 'consulta') {
      return (
        <tr key={log.fecha} className="hover:bg-gray-50">
          <td className="px-4 py-2 border">{log.usuario}</td>
          <td className="px-4 py-2 border">Consulta</td>
          <td className="px-4 py-2 border">
            <div>
              <strong>Pregunta:</strong>
              <pre className="whitespace-pre-wrap">{log.pregunta}</pre>
            </div>
            <div className="mt-2">
              <strong>SQL:</strong>
              <pre className="whitespace-pre-wrap text-sm bg-gray-100 p-2 rounded">{log.sql}</pre>
            </div>
            <div className="mt-2">
              <strong>Respuesta:</strong>
              <pre className="whitespace-pre-wrap">{log.respuesta}</pre>
            </div>
          </td>
          <td className="px-4 py-2 border">{new Date(log.fecha).toLocaleString()}</td>
        </tr>
      );
    } else {
      return (
        <tr key={log.fecha} className="hover:bg-gray-50">
          <td className="px-4 py-2 border">{log.usuario}</td>
          <td className="px-4 py-2 border">
            {log.accion.charAt(0).toUpperCase() + log.accion.slice(1)}
          </td>
          <td className="px-4 py-2 border">
            <div>
              <strong>Módulo:</strong> {log.modulo}
            </div>
            <div className="mt-2">
              <strong>Detalles:</strong>
              <pre className="whitespace-pre-wrap text-sm bg-gray-100 p-2 rounded mt-1">
                {JSON.stringify(log.detalles, null, 2)}
              </pre>
            </div>
          </td>
          <td className="px-4 py-2 border">{new Date(log.fecha).toLocaleString()}</td>
        </tr>
      );
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Logs del Sistema</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-4 py-2 border">Usuario</th>
              <th className="px-4 py-2 border">Tipo</th>
              <th className="px-4 py-2 border">Detalles</th>
              <th className="px-4 py-2 border">Fecha</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => renderLogContent(log))}
          </tbody>
        </table>
      </div>
    </div>
  );
}