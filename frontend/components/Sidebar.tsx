// frontend/components/Sidebar.tsx
"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import { cn } from "@/lib/utils";

interface TokenData {
  sub: string;
  role: string;  // Ya no es opcional
  exp: number;
}

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [loading, setLoading] = useState(true);

  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const checkAuth = () => {
      // Solo ejecutar en el cliente
      if (typeof window === 'undefined') {
        return;
      }

      const storedToken = localStorage.getItem("token");
      setToken(storedToken);
      
      if (!storedToken) {
        console.log("No hay token almacenado");
        setIsSuperuser(false);
        setLoading(false);
        return;
      }

      try {
        const decoded = jwtDecode<TokenData>(storedToken);
        
        // Verificar si el token ha expirado
        const currentTime = Math.floor(Date.now() / 1000);
        if (decoded.exp && decoded.exp < currentTime) {
          console.error("Token expirado");
          handleLogout();
          return;
        }

        // Verificar el rol explícitamente
        if (!decoded.role) {
          console.error("Token no contiene rol");
          setIsSuperuser(false);
        } else {
          const isSuperuserRole = decoded.role.toLowerCase() === "superuser";
          setIsSuperuser(isSuperuserRole);
        }

        // Configurar el token en el cliente API
        api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        setLoading(false);
      } catch (error) {
        console.error("Error al decodificar el token:", error);
        handleLogout();
      }
    };

    // Ejecutar inmediatamente
    checkAuth();

    // Configurar un intervalo para verificar periódicamente
    const interval = setInterval(checkAuth, 30000); // Verificar cada 30 segundos

    // Limpiar el intervalo cuando el componente se desmonte
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    // Limpiar token de localStorage
    localStorage.removeItem("token");
    // Limpiar token de cookie
    document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT";
    // Limpiar estado local
    setToken(null);
    setIsSuperuser(false);
    setLoading(false);
    // Limpiar headers de API
    delete api.defaults.headers.common['Authorization'];
    // Redirigir a la página principal
    window.location.href = "/";
  };


  if (loading) {
    return (
      <aside className="w-64 bg-white shadow-md flex flex-col p-4">
        <h2 className="text-xl font-bold mb-6">IA Multifuente</h2>
        <div className="flex justify-center items-center h-full">
          <p>Cargando...</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-64 bg-white shadow-md flex flex-col p-4">
      <h2 className="text-xl font-bold mb-6">IA Multifuente</h2>
      <nav className="flex flex-col gap-2">
        {token && (
          <>
            <Button
              className={cn(
                "text-white transition-all duration-200 shadow-sm",
                pathname === "/consultas"
                  ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                  : "bg-blue-500 hover:bg-blue-600"
              )}
              onClick={() => router.push("/consultas")}
            >
              Consultas
            </Button>
            
            {isSuperuser && (
              <div className="flex flex-col gap-2">
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/documentos"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/documentos")}
                >
                  Documentos
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/logs"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/logs")}
                >
                  Logs
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/llm-config"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/llm-config")}
                >
                  Configurar API LLM
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/document-config"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/document-config")}
                >
                  Configurar Subida de Documentos
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/config/sql-server"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/config/sql-server")}
                >
                  Configurar SQL Server
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/users"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/users")}
                >
                  Gestión de Usuarios
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/config"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/config")}
                >
                  Configuración General
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/reports"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/reports")}
                >
                  Informes
                </Button>
                <Button
                  className={cn(
                    "text-white transition-all duration-200 shadow-sm",
                    pathname === "/admin/analytics"
                      ? "bg-purple-600 hover:bg-purple-700 text-lg font-bold scale-105"
                      : "bg-blue-500 hover:bg-blue-600"
                  )}
                  onClick={() => router.push("/admin/analytics")}
                >
                  Analíticas
                </Button>
              </div>
            )}
          </>
        )}
        <Button
          className="bg-red-500 hover:bg-red-600 transition-colors duration-200 shadow-sm mt-4 text-white"
          onClick={handleLogout}
        >
          Cerrar sesión
        </Button>
      </nav>
    </aside>
  );
}
