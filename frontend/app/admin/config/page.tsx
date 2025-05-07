"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import api from "@/lib/api";

interface SystemInfo {
  documentConfig: {
    max_file_size: number;
    allowed_extensions: string;
    max_files_per_upload: number;
    storage_path: string;
  } | null;
  sqlConfig: {
    server: string;
    database: string;
    driver: string;
  } | null;
  llmCount: number;
  userCount: number;
}

export default function SystemConfigPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({
    documentConfig: null,
    sqlConfig: null,
    llmCount: 0,
    userCount: 0
  });
  const [error, setError] = useState("");

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const [docConfig, sqlConfig, users, llmCount] = await Promise.all([
        api.get("/admin/document-config"),
        api.get("/admin/sql-config"),
        api.get("/admin/users"),
        api.get("/admin/llm/count")
      ]);

      setSystemInfo({
        documentConfig: docConfig.data,
        sqlConfig: sqlConfig.data,
        userCount: users.data.length,
        llmCount: llmCount.data.count
      });
    } catch (err) {
      setError("Error al cargar la información del sistema");
      console.error(err);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold mb-8">Configuración del Sistema</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Tarjetas de acceso rápido */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Link href="/admin/llm-config" className="block">
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-4">Configuración de LLMs</h2>
            <p className="text-gray-600">Gestiona los modelos de lenguaje y sus configuraciones</p>
          </div>
        </Link>

        <Link href="/admin/document-config" className="block">
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-4">Configuración de Documentos</h2>
            <p className="text-gray-600">Configura las opciones de gestión de documentos</p>
          </div>
        </Link>

        <Link href="/admin/config/sql-server" className="block">
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-4">Configuración SQL Server</h2>
            <p className="text-gray-600">Gestiona la conexión con SQL Server</p>
          </div>
        </Link>

        <Link href="/admin/users" className="block">
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-4">Gestión de Usuarios</h2>
            <p className="text-gray-600">Administra los usuarios del sistema</p>
          </div>
        </Link>
      </div>

      {/* Información del sistema */}
      <div className="mt-12">
        <h2 className="text-2xl font-semibold mb-6">Estado del Sistema</h2>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Documentos</h3>
              {systemInfo.documentConfig ? (
                <div className="space-y-2">
                  <p>Tamaño máximo de archivo: {systemInfo.documentConfig.max_file_size} MB</p>
                  <p>Extensiones permitidas: {systemInfo.documentConfig.allowed_extensions}</p>
                  <p>Máximo archivos por carga: {systemInfo.documentConfig.max_files_per_upload}</p>
                  <p>Ruta de almacenamiento: {systemInfo.documentConfig.storage_path}</p>
                </div>
              ) : (
                <p className="text-gray-500">No hay configuración de documentos</p>
              )}
            </div>

            <div>
              <h3 className="text-lg font-medium mb-4">Base de Datos</h3>
              {systemInfo.sqlConfig ? (
                <div className="space-y-2">
                  <p>Servidor: {systemInfo.sqlConfig.server}</p>
                  <p>Base de datos: {systemInfo.sqlConfig.database}</p>
                  <p>Driver: {systemInfo.sqlConfig.driver}</p>
                </div>
              ) : (
                <p className="text-gray-500">No hay configuración de SQL Server</p>
              )}
            </div>

            <div>
              <h3 className="text-lg font-medium mb-4">Estadísticas</h3>
              <div className="space-y-2">
                <p>Usuarios registrados: {systemInfo.userCount}</p>
                <p>Modelos LLM configurados: {systemInfo.llmCount}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}