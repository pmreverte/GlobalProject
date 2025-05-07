"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface LLMConfig {
  id: number;
  name: string;
  provider: string;
  model_name: string;
  api_key: string;
  temperature: string;
  is_active: boolean;
  is_default: boolean;
}

export default function LLMConfigPage() {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [newConfig, setNewConfig] = useState<Omit<LLMConfig, 'id'>>({
    name: "",
    provider: "",
    model_name: "",
    api_key: "",
    temperature: "0",
    is_active: true,
    is_default: false,
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      const response = await api.get("/llm/config");
      setConfigs(response.data);
    } catch (err) {
      setError("Error al cargar las configuraciones");
      console.error(err);
    }
  };

  const handleSubmit = async () => {
    try {
      setError("");
      setSuccess("");

      // Validaciones básicas
      if (!newConfig.name || !newConfig.provider || !newConfig.model_name || !newConfig.api_key) {
        setError("Por favor, complete todos los campos requeridos");
        return;
      }

      await api.post("/llm/config", newConfig);
      setSuccess("Configuración guardada exitosamente");
      loadConfigs();
      
      // Limpiar el formulario
      setNewConfig({
        name: "",
        provider: "",
        model_name: "",
        api_key: "",
        temperature: "0",
        is_active: true,
        is_default: false,
      });
    } catch (err) {
      setError("Error al guardar la configuración");
      console.error(err);
    }
  };

  const handleUpdate = async (id: number, config: LLMConfig) => {
    try {
      setError("");
      setSuccess("");
      await api.put(`/llm/config/${id}`, config);
      setSuccess("Configuración actualizada exitosamente");
      loadConfigs();
    } catch (err) {
      setError("Error al actualizar la configuración");
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("¿Está seguro de eliminar esta configuración?")) {
      return;
    }

    try {
      setError("");
      setSuccess("");
      await api.delete(`/llm/config/${id}`);
      setSuccess("Configuración eliminada exitosamente");
      loadConfigs();
    } catch (err) {
      setError("Error al eliminar la configuración");
      console.error(err);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold">Configuración de LLMs</h1>

      {/* Mensajes de error y éxito */}
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error}</div>}
      {success && <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">{success}</div>}

      {/* Formulario para nueva configuración */}
      <div className="bg-white p-6 rounded-lg shadow-md space-y-4">
        <h2 className="text-xl font-semibold">Nueva Configuración</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            placeholder="Nombre"
            value={newConfig.name}
            onChange={(e) => setNewConfig({ ...newConfig, name: e.target.value })}
          />
          <Input
            placeholder="Proveedor (ej: openai, anthropic)"
            value={newConfig.provider}
            onChange={(e) => setNewConfig({ ...newConfig, provider: e.target.value })}
          />
          <Input
            placeholder="Nombre del modelo (ej: gpt-4)"
            value={newConfig.model_name}
            onChange={(e) => setNewConfig({ ...newConfig, model_name: e.target.value })}
          />
          <Input
            type="password"
            placeholder="API Key"
            value={newConfig.api_key}
            onChange={(e) => setNewConfig({ ...newConfig, api_key: e.target.value })}
          />
          <Input
            type="number"
            placeholder="Temperatura (0-1)"
            value={newConfig.temperature}
            onChange={(e) => setNewConfig({ ...newConfig, temperature: e.target.value })}
          />
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={newConfig.is_active}
                onChange={(e) => setNewConfig({ ...newConfig, is_active: e.target.checked })}
                className="form-checkbox"
              />
              <span>Activo</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={newConfig.is_default}
                onChange={(e) => setNewConfig({ ...newConfig, is_default: e.target.checked })}
                className="form-checkbox"
              />
              <span>Por defecto</span>
            </label>
          </div>
        </div>
        <Button onClick={handleSubmit} className="mt-4">Guardar Configuración</Button>
      </div>

      {/* Lista de configuraciones existentes */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Configuraciones Existentes</h2>
        {configs.map((config) => (
          <div key={config.id} className="bg-white p-6 rounded-lg shadow-md space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                placeholder="Nombre"
                value={config.name}
                onChange={(e) => handleUpdate(config.id, { ...config, name: e.target.value })}
              />
              <Input
                placeholder="Proveedor"
                value={config.provider}
                onChange={(e) => handleUpdate(config.id, { ...config, provider: e.target.value })}
              />
              <Input
                placeholder="Nombre del modelo"
                value={config.model_name}
                onChange={(e) => handleUpdate(config.id, { ...config, model_name: e.target.value })}
              />
              <Input
                type="password"
                placeholder="API Key"
                value={config.api_key}
                onChange={(e) => handleUpdate(config.id, { ...config, api_key: e.target.value })}
              />
              <Input
                type="number"
                placeholder="Temperatura"
                value={config.temperature}
                onChange={(e) => handleUpdate(config.id, { ...config, temperature: e.target.value })}
              />
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.is_active}
                    onChange={(e) => handleUpdate(config.id, { ...config, is_active: e.target.checked })}
                    className="form-checkbox"
                  />
                  <span>Activo</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.is_default}
                    onChange={(e) => handleUpdate(config.id, { ...config, is_default: e.target.checked })}
                    className="form-checkbox"
                  />
                  <span>Por defecto</span>
                </label>
                <Button
                  onClick={() => handleDelete(config.id)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Eliminar
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}