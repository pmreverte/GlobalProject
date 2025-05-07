'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Alert, AlertDescription } from "./ui/alert";
import { Loader2 } from "lucide-react";
import { FeedbackRespuesta } from './FeedbackRespuesta';

interface LLMConfig {
  id: number;
  name: string;
  provider: string;
  model_name: string;
  is_default: boolean;
}

interface Message {
  type: 'pregunta' | 'respuesta';
  content: string;
  sql_generado?: string;
  timestamp?: string;
  conversation_id?: number;
  feedback?: {
    fue_util: boolean;
  };
}

interface GroupedConversation {
  date: string;
  conversations: {
    id: number;
    messages: Message[];
    timestamp: string;
  }[];
}

export default function ChatBox() {
  const [pregunta, setPregunta] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [llms, setLLMs] = useState<LLMConfig[]>([]);
  const [selectedLLM, setSelectedLLM] = useState<string>('');
  const [conversationHistory, setConversationHistory] = useState<Message[]>([]);
  const [groupedHistory, setGroupedHistory] = useState<GroupedConversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);

  // Función para agrupar conversaciones por fecha
  const groupConversationsByDate = (messages: Message[]) => {
    const grouped = messages.reduce((acc: { [key: string]: any }, message) => {
      if (!message.timestamp || !message.conversation_id) return acc;
      
      const date = new Date(message.timestamp).toLocaleDateString();
      if (!acc[date]) {
        acc[date] = {
          date,
          conversations: {}
        };
      }
      
      if (!acc[date].conversations[message.conversation_id]) {
        acc[date].conversations[message.conversation_id] = {
          id: message.conversation_id,
          messages: [],
          timestamp: message.timestamp
        };
      }
      
      acc[date].conversations[message.conversation_id].messages.push(message);
      return acc;
    }, {});

    return Object.values(grouped).map(group => ({
      ...group,
      conversations: Object.values(group.conversations).sort((a: any, b: any) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )
    })).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  };

  // Cargar el historial de conversación al iniciar
  useEffect(() => {
    const fetchHistorial = async () => {
      try {
        const response = await api.get('/api/query/historial');
        const data = response.data;
        setConversationHistory(data.historial);
        setGroupedHistory(groupConversationsByDate(data.historial));
      } catch (error) {
        setError('Error al cargar el historial de conversación');
      }
    };

    fetchHistorial();
  }, []);

  useEffect(() => {
    const loadLLMs = async () => {
      try {
        const response = await api.get('/api/llm/active');
        const data = response.data;
        setLLMs(data);
        
        // Seleccionar el LLM por defecto
        const defaultLLM = data.find((llm: LLMConfig) => llm.is_default);
        setSelectedLLM(defaultLLM?.id.toString() ?? data[0]?.id.toString() ?? '');
      } catch (error) {
        setError('Error al cargar los modelos LLM. Por favor, recargue la página.');
      }
    };

    loadLLMs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pregunta.trim() || !selectedLLM) return;

    setIsLoading(true);
    setError('');
    
    const currentQuestion = pregunta.trim();
    
    try {
      const response = await api.post('/api/query/inteligente', {
        pregunta: currentQuestion,
        llm_id: parseInt(selectedLLM)
      });

      const data = response.data;
      
      // Actualizar el historial después de una nueva consulta
      const historialResponse = await api.get('/api/query/historial');
      const historialData = historialResponse.data;
      setConversationHistory(historialData.historial);
      setGroupedHistory(groupConversationsByDate(historialData.historial));
      setSelectedConversationId(null); // Reset selected conversation to show current chat
      
      // Clear input after successful query
      setPregunta('');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Error al procesar la consulta. Por favor, inténtelo de nuevo.');
    } finally {
      setIsLoading(false);
    }
  };

  // Obtener la última pregunta y respuesta
  const lastQuestion = conversationHistory.find(m => m.type === 'pregunta');
  const lastResponse = conversationHistory.find(m => m.type === 'respuesta');

  return (
    <div>
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <div className="w-full sm:w-1/3">
          <select
            className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring focus:border-blue-500"
            value={selectedLLM}
            onChange={(e) => setSelectedLLM(e.target.value)}
          >
            <option value="" disabled>Seleccione un modelo LLM</option>
            {llms.map((llm) => (
              <option key={llm.id} value={llm.id.toString()}>
                {llm.name} ({llm.model_name})
                {llm.is_default && " - Por defecto"}
              </option>
            ))}
          </select>
        </div>
        <div className="w-full sm:flex-1 flex gap-4">
          <input
            className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring focus:border-blue-500"
            placeholder="Ej: ¿Cuál fue la última venta en Europa?"
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            disabled={isLoading}
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !pregunta.trim() || !selectedLLM}
            className="font-medium rounded transition py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Consultar'}
          </button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="mt-6 grid grid-cols-12 gap-6 h-[600px]">
        {/* Chat History Sidebar */}
        <div className="col-span-4 overflow-y-auto border border-gray-200 rounded-xl bg-gray-50 p-4">
          {groupedHistory.map((group) => (
            <div key={group.date} className="mb-6">
              <h3 className="text-sm font-semibold text-gray-500 mb-2">{group.date}</h3>
              {group.conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConversationId(conv.id)}
                  className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                    selectedConversationId === conv.id
                      ? 'bg-blue-100 border border-blue-200'
                      : 'hover:bg-gray-100 border border-gray-200'
                  }`}
                >
                  <p className="text-sm font-medium truncate">
                    {conv.messages.find(m => m.type === 'pregunta')?.content || 'Sin pregunta'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(conv.timestamp).toLocaleTimeString()}
                  </p>
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Current Chat Area */}
        <div className="col-span-8 overflow-y-auto border border-gray-200 rounded-xl bg-gray-50 p-4">
          {(selectedConversationId === null ? conversationHistory :
            conversationHistory.filter(m => m.conversation_id === selectedConversationId))
            .map((message, index) => (
            <div key={index} className={`mb-4 ${message.type === 'pregunta' ? 'ml-auto max-w-[80%]' : 'mr-auto max-w-[80%]'}`}>
              <div className={`p-4 rounded-xl ${
                message.type === 'pregunta'
                  ? 'bg-blue-600 text-white ml-auto'
                  : 'bg-white border border-gray-200 shadow-sm'
              }`}>
                {message.type === 'pregunta' ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <>
                    <h2 className="font-semibold text-lg mb-2">📌 Respuesta:</h2>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <div className="mt-4">
                      <FeedbackRespuesta
                        pregunta={conversationHistory.find(m => m.type === 'pregunta' && m.conversation_id === message.conversation_id)?.content || ''}
                        llmId={parseInt(selectedLLM)}
                        feedback={message.feedback}
                      />
                    </div>
                  </>
                )}
              </div>
              {message.timestamp && (
                <div className={`text-xs text-gray-500 mt-1 ${message.type === 'pregunta' ? 'text-right' : 'text-left'}`}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}