"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { jwtDecode } from "jwt-decode";

interface TokenData {
  sub: string;
  role: string;
  exp: number;
}

// Extend HTMLInputElement to include webkitdirectory
declare module 'react' {
  interface HTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    webkitdirectory?: string;
    directory?: string;
  }
}

export default function DocumentosAdmin() {
  const [archivos, setArchivos] = useState<File[]>([]);
  const [documentos, setDocumentos] = useState<string[]>([]);
  const [mensaje, setMensaje] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isSuperUser, setIsSuperUser] = useState(false);
  const [uploadMode, setUploadMode] = useState<'file' | 'folder'>('file');

  useEffect(() => {
    const controller = new AbortController();

    const checkAuthAndLoadDocs = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem("token");
        
        if (!token) {
          window.location.href = "/login";
          return;
        }

        // Verify role from token
        const decoded = jwtDecode<TokenData>(token);
        
        // Check token expiration
        const currentTime = Math.floor(Date.now() / 1000);
        if (decoded.exp && decoded.exp < currentTime) {
          localStorage.removeItem("token");
          window.location.href = "/login";
          return;
        }

        // Check role
        if (decoded.role !== "superuser") {
          setMensaje("No tienes permisos para acceder a esta página. Se requiere rol de superusuario.");
          setIsSuperUser(false);
          return;
        }
        
        setIsSuperUser(true);
        
        // Ensure the token is set in the API client
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        // Load documents
        const res = await api.get("/query/documentos/listar", {
          signal: controller.signal
        });
        setDocumentos(res.data.documentos || []);
        setMensaje(""); // Limpiar mensajes de error previos
      } catch (error: any) {
        console.error("Error al cargar documentos:", error);
        if (error.name === "InvalidTokenError" || error.response?.status === 401) {
          localStorage.removeItem("token");
          delete api.defaults.headers.common['Authorization'];
          window.location.href = "/login";
        } else {
          setMensaje("Error al cargar los documentos. Por favor, intente de nuevo.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    // Check auth and load docs immediately
    checkAuthAndLoadDocs();

    // Set up interval to periodically check auth and refresh docs
    const interval = setInterval(checkAuthAndLoadDocs, 30000);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  const listar = async () => {
    try {
      const res = await api.get("/query/documentos/listar");
      setDocumentos(res.data.documentos || []);
      setMensaje(""); // Limpiar mensaje de error si la carga fue exitosa
    } catch (error: any) {
      console.error("Error al listar documentos:", error);
      if (error.response?.status !== 401) { // No mostrar mensaje si es error de auth
        setMensaje("No se pudieron cargar los documentos.");
      }
    }
  };

  const procesarArchivos = async () => {
    if (archivos.length === 0) {
      setMensaje("Por favor, seleccione archivos o una carpeta.");
      return;
    }

    setIsUploading(true);
    setMensaje(`Subiendo ${archivos.length} archivo(s)...`);

    const formData = new FormData();
    archivos.forEach(archivo => {
      // Mantener la estructura de carpetas usando el path relativo
      const relativePath = archivo.webkitRelativePath || archivo.name;
      formData.append("archivos", archivo, relativePath);
    });

    try {
      const endpoint = uploadMode === 'folder' ? 
        "/query/documentos/cargar-carpeta" : 
        "/query/documentos/cargar";
      
      const res = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setMensaje("Archivos subidos exitosamente. Actualizando lista...");
      setArchivos([]);
      // Limpiar los inputs
      const fileInputs = document.querySelectorAll('input[type="file"]') as NodeListOf<HTMLInputElement>;
      fileInputs.forEach(input => input.value = '');
      
      // Pequeña pausa antes de actualizar la lista para mejor feedback visual
      await new Promise(resolve => setTimeout(resolve, 500));
      await listar();
      setMensaje(res.data.resultado);
    } catch (error: any) {
      console.error("Error al subir documentos:", error);
      if (error.response?.status !== 401) { // No mostrar mensaje si es error de auth
        setMensaje(error.response?.data?.mensaje || "Error al subir los documentos. Por favor, intente de nuevo.");
      }
    } finally {
      setIsUploading(false);
    }
  };

  const eliminar = async (nombre: string) => {
    try {
      const res = await api.delete(`/query/documentos/eliminar/${nombre}`);
      setMensaje(res.data.mensaje);
      await listar();
    } catch (error: any) {
      console.error("Error al eliminar documento:", error);
      if (error.response?.status !== 401) { // No mostrar mensaje si es error de auth
        setMensaje(error.response?.data?.mensaje || "No se pudo eliminar el documento. Por favor, intente de nuevo.");
      }
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 p-6">
      <h1 className="text-2xl font-bold">Administración de Documentos</h1>
      
      {mensaje && (
        <div className={`text-sm ${
          mensaje.toLowerCase().includes('error') ? 'text-red-600' : 'text-blue-700'
        } mb-4`}>
          {mensaje}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center items-center min-h-[200px]">
          <div className="text-gray-600">Cargando documentos...</div>
        </div>
      ) : isSuperUser ? (
        <>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <select 
                className="border rounded p-2"
                value={uploadMode}
                onChange={(e) => setUploadMode(e.target.value as 'file' | 'folder')}
                disabled={isLoading || isUploading}
              >
                <option value="file">Archivos individuales</option>
                <option value="folder">Carpeta completa</option>
              </select>
            </div>

            <div className="flex items-center gap-4">
              {uploadMode === 'file' ? (
                <Input
                  type="file"
                  multiple
                  onChange={(e) => setArchivos(Array.from(e.target.files || []))}
                  disabled={isLoading || isUploading}
                />
              ) : (
                <Input
                  type="file"
                  webkitdirectory="true"
                  directory="true"
                  multiple
                  onChange={(e) => setArchivos(Array.from(e.target.files || []))}
                  disabled={isLoading || isUploading}
                />
              )}
              <Button
                onClick={procesarArchivos}
                disabled={isLoading || isUploading || archivos.length === 0}
              >
                {isUploading ? 'Subiendo...' : 'Subir'}
              </Button>
            </div>
          </div>

          <h2 className="text-lg font-semibold mt-6">Documentos cargados</h2>
          {documentos.length === 0 ? (
            <div className="text-gray-500 text-center py-4">
              No hay documentos cargados
            </div>
          ) : (
            <ul className="space-y-2">
              {documentos.map((doc) => (
                <li key={doc} className="flex justify-between items-center bg-white p-2 rounded shadow">
                  <span className="break-all pr-4">{doc}</span>
                  <Button
                    className="bg-red-600 hover:bg-red-700 shrink-0"
                    onClick={() => eliminar(doc)}
                    disabled={isLoading || isUploading}
                  >
                    Eliminar
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <div className="text-center py-8 text-gray-600">
          No tienes permisos para acceder a esta página.
          <br />
          Se requiere rol de superusuario.
        </div>
      )}
    </div>
  );
}
