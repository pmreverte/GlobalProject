// frontend/app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { jwtDecode } from "jwt-decode";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AxiosError } from "axios";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async () => {
    try {
      // Validación básica
      if (!username || !password) {
        setError("Por favor, complete todos los campos");
        return;
      }

      // Crear FormData para enviar los datos en el formato correcto
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      console.log('Iniciando solicitud de login...');
      const res = await api.post("/auth/token",
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      console.log('Respuesta recibida:', res.data);
      const { access_token } = res.data;
      
      if (!access_token) {
        console.error('Token no recibido en la respuesta');
        setError("Error: Token no recibido del servidor");
        return;
      }

      try {
        // Decodificar el token para verificar su estructura
        const decoded = jwtDecode<{ sub: string; role: string; exp: number }>(access_token);
        console.log('Token decodificado:', { ...decoded, exp: new Date(decoded.exp * 1000).toISOString() });
        
        // Verificar campos requeridos
        if (!decoded.sub || !decoded.role || !decoded.exp) {
          console.error('Token malformado:', decoded);
          setError("Error: Token malformado");
          return;
        }

        // Verificar expiración
        const currentTime = Math.floor(Date.now() / 1000);
        if (decoded.exp < currentTime) {
          console.error('Token expirado:', {
            expTime: new Date(decoded.exp * 1000).toISOString(),
            currentTime: new Date(currentTime * 1000).toISOString()
          });
          setError("Error: Token expirado");
          return;
        }

        // Guardar token en localStorage para API calls
        localStorage.setItem("token", access_token);
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        // Guardar token en cookie para middleware
        document.cookie = `token=${access_token}; path=/`;
        
        // Redirigir a la página de consultas
        window.location.href = "/consultas";
        
      } catch (tokenError) {
        console.error("Error al decodificar el token:", tokenError);
        setError("Error: Token inválido recibido del servidor");
        return;
      }

    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 401) {
          setError("Credenciales incorrectas");
        } else if (err.response?.status === 422) {
          setError("Datos de inicio de sesión inválidos");
        } else if (!err.response) {
          setError("Error de conexión con el servidor");
        } else {
          setError("Error en el inicio de sesión");
        }
        console.error("Error de login:", err.response?.data);
      } else {
        setError("Error inesperado durante el inicio de sesión");
        console.error("Error inesperado:", err);
      }
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-sm p-6 bg-white rounded-2xl shadow-xl space-y-6">
        <h1 className="text-2xl font-bold text-center">Iniciar sesión</h1>
        {error && <div className="text-red-500 text-sm">{error}</div>}
        <Input
          type="text"
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <Input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button onClick={handleLogin} className="w-full">
          Entrar
        </Button>
      </div>
    </div>
  );
}