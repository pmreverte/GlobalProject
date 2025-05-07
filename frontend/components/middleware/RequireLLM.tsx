'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

interface Props {
  children: React.ReactNode;
}

export default function RequireLLM({ children }: Props) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasActiveLLMs, setHasActiveLLMs] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const checkLLMs = async () => {
      try {
        const response = await api.get('/llm/has-active');
        setHasActiveLLMs(response.data.has_active_llms);
      } catch (error) {
        console.error('Error checking LLMs:', error);
        setHasActiveLLMs(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkLLMs();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Verificando configuración...</div>
      </div>
    );
  }

  useEffect(() => {
    if (!isLoading && !hasActiveLLMs) {
      router.push('/admin/llm-config');
    }
  }, [isLoading, hasActiveLLMs, router]);

  if (!hasActiveLLMs) {
    return null;
  }

  return <>{children}</>;
}