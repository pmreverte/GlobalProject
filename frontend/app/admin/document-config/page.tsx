"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface DocumentConfig {
  id: number;
  max_file_size: number; // in MB
  allowed_extensions: string;
  max_files_per_upload: number;
  storage_path: string;
  is_active: boolean;
}

export default function DocumentConfigPage() {
  const [config, setConfig] = useState<DocumentConfig | null>(null);
  const [newConfig, setNewConfig] = useState<Omit<DocumentConfig, 'id'>>({
    max_file_size: 10,
    allowed_extensions: ".pdf,.doc,.docx,.txt",
    max_files_per_upload: 5,
    storage_path: "uploads/",
    is_active: true,
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await api.get("/admin/document-config");
      setConfig(response.data);
      if (response.data) {
        setNewConfig(response.data);
      }
    } catch (err) {
      setError("Error al cargar la configuración");
      console.error(err);
    }
  };

  const handleSubmit = async () => {
    try {
      setError("");
      setSuccess("");

      // Validaciones básicas
      if (newConfig.max_file_size <= 0 || newConfig.max_files_per_upload <= 0) {
        setError("Los valores deben ser mayores que 0");
        return;
      }

      if (!newConfig.allowed_extensions) {
        setError("Debe especificar las extensiones permitidas");
        return;
      }

      if (!newConfig.storage_path) {
        setError("Debe especificar la ruta de almacenamiento");
        return;
      }

      if (config) {
        // Actualizar configuración existente
        await api.put("/admin/document-config", newConfig);
      } else {
        // Crear nueva configuración
        await api.post("/admin/document-config", newConfig);
      }
      
      setSuccess("Configuración guardada exitosamente");
      loadConfig();
    } catch (err) {
      setError("Error al guardar la configuración");
      console.error(err);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold">Configuración de Documentos</h1>

      {/* Mensajes de error y éxito */}
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error}</div>}
      {success && <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">{success}</div>}

      {/* Formulario de configuración */}
      <div className="bg-white p-6 rounded-lg shadow-md space-y-4">
        <h2 className="text-xl font-semibold">Configuración de Subida de Documentos</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tamaño máximo de archivo (MB)
            </label>
            <Input
              type="number"
              value={newConfig.max_file_size}
              onChange={(e) => setNewConfig({ ...newConfig, max_file_size: Number(e.target.value) })}
              min="1"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Extensiones permitidas
            </label>
            <Input
              placeholder="ej: .pdf,.doc,.docx,.txt"
              value={newConfig.allowed_extensions}
              onChange={(e) => setNewConfig({ ...newConfig, allowed_extensions: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Máximo de archivos por subida
            </label>
            <Input
              type="number"
              value={newConfig.max_files_per_upload}
              onChange={(e) => setNewConfig({ ...newConfig, max_files_per_upload: Number(e.target.value) })}
              min="1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ruta de almacenamiento
            </label>
            <Input
              placeholder="ej: uploads/"
              value={newConfig.storage_path}
              onChange={(e) => setNewConfig({ ...newConfig, storage_path: e.target.value })}
            />
          </div>

          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={newConfig.is_active}
                onChange={(e) => setNewConfig({ ...newConfig, is_active: e.target.checked })}
                className="form-checkbox"
              />
              <span>Subida de documentos activa</span>
            </label>
          </div>
        </div>

        <Button onClick={handleSubmit} className="mt-4">
          {config ? "Actualizar Configuración" : "Guardar Configuración"}
        </Button>
      </div>
    </div>
  );
}