"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';
import api from '@/lib/api';

interface TokenData {
  sub: string;
  role: string;
  exp: number;
}

export default function VerifyAuth() {
  const router = useRouter();

  useEffect(() => {
    const verifyAndRedirect = async () => {
      try {
        const token = localStorage.getItem('token');
        
        if (!token) {
          router.replace('/login');
          return;
        }

        const decoded = jwtDecode<TokenData>(token);
        const currentTime = Math.floor(Date.now() / 1000);

        if (decoded.exp && decoded.exp < currentTime) {
          localStorage.removeItem('token');
          router.replace('/login');
          return;
        }

        // Configurar el token en el cliente API
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        // Redirigir a la página principal
        window.location.href = '/';
      } catch (error) {
        console.error('Error al verificar el token:', error);
        localStorage.removeItem('token');
        router.replace('/login');
      }
    };

    verifyAndRedirect();
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
  );
}