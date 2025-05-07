"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { InfoCircledIcon, Pencil1Icon, TrashIcon } from "@radix-ui/react-icons";
import { Tooltip } from "@/components/ui/tooltip";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

type SQLConfig = {
  id?: number;
  username: string;
  password: string;
  server: string;
  database: string;
  driver: string;
  use_windows_auth: boolean;
  is_active?: boolean;
};

const COMMON_DRIVERS = [
  "ODBC Driver 18 for SQL Server",
  "ODBC Driver 17 for SQL Server",
  "SQL Server Native Client 11.0",
  "SQL Server"
];

const CONNECTION_HELP = {
  server: "Nombre del servidor SQL Server. Para instancias nombradas use SERVIDOR\\INSTANCIA",
  database: "Nombre de la base de datos a la que desea conectarse",
  windows_auth: "Use la autenticación de Windows en lugar de usuario/contraseña",
  username: "Nombre de usuario SQL Server (no necesario para autenticación Windows)",
  password: "Contraseña SQL Server (no necesaria para autenticación Windows)",
  driver: "Driver ODBC para SQL Server. Se recomienda usar la versión más reciente disponible"
};

export default function SQLServerConfig() {
  const [configs, setConfigs] = useState<SQLConfig[]>([]);
  const [config, setConfig] = useState<SQLConfig>({
    username: "",
    password: "",
    server: "",
    database: "",
    driver: "ODBC Driver 17 for SQL Server",
    use_windows_auth: false
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [progress, setProgress] = useState<{total: number; processed: number} | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const response = await api.get("/api/admin/sql-config", {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setConfigs(response.data.configs || []);
    } catch (error) {
      console.error("Error al cargar las configuraciones:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      // Ensure we're using the existing SQL_SERVER_URL connection
      const submitData: {
        id?: number;
        server: string;
        database: string;
        driver: string;
        use_windows_auth: boolean;
        username?: string;
        password?: string;
      } = {
        ...(config.id ? { id: config.id } : {}),
        server: config.server,
        database: config.database,
        driver: config.driver,
        use_windows_auth: config.use_windows_auth,
        ...(config.use_windows_auth ? {} : {
          username: config.username,
          password: config.password
        })
      };

      const response = await api.post("/api/admin/sql-config", submitData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = response.data;

      if (response.status === 200) {
        // Update the config with the returned ID if it's a new config
        if (data.id) {
          setConfig(prev => ({ ...prev, id: data.id }));
        }
        setMessage({ type: "success", text: "Configuración guardada exitosamente. Use 'Probar conexión' para activarla." });
        
        // Recargar las configuraciones
        await fetchConfigs();
      } else {
        setMessage({ type: "error", text: data.error || "Error al guardar la configuración" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "Error al conectar con el servidor" });
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      // First save the configuration if it's new
      if (!config.id) {
        const saveData: {
          id?: number;
          server: string;
          database: string;
          driver: string;
          use_windows_auth: boolean;
          username?: string;
          password?: string;
        } = {
          ...(config.id ? { id: config.id } : {}),
          server: config.server,
          database: config.database,
          driver: config.driver,
          use_windows_auth: config.use_windows_auth,
          ...(config.use_windows_auth ? {} : {
            username: config.username,
            password: config.password
          })
        };

        const saveResponse = await api.post("/api/admin/sql-config", saveData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        if (saveResponse.data.id) {
          setConfig(prev => ({ ...prev, id: saveResponse.data.id }));
        }
      }

      // Then test the connection
      // Preparar solo los datos necesarios para la prueba
      const testData: {
        id?: number;
        server: string;
        database: string;
        driver: string;
        use_windows_auth: boolean;
        username?: string;
        password?: string;
      } = {
        ...(config.id ? { id: config.id } : {}),
        server: config.server,
        database: config.database,
        driver: config.driver,
        use_windows_auth: config.use_windows_auth,
        ...(config.use_windows_auth ? {} : {
          username: config.username,
          password: config.password
        })
      };

      console.log('Datos de prueba:', testData);

      setProgress(null);
      setMessage({ type: "info", text: "Probando conexión y generando embeddings. Este proceso puede tardar varios minutos..." });
      
      const testResponse = await api.post("/api/admin/sql-config/test", testData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (testResponse.data.progress) {
        setProgress(testResponse.data.progress);
      }
      
      setMessage({
        type: "success",
        text: testResponse.data.message || "Conexión exitosa y embeddings generados correctamente"
      });
      
      // Reload configurations after successful test since it may have changed active status
      await fetchConfigs();
    } catch (error) {
      setMessage({ type: "error", text: error instanceof Error ? error.message : "Error al conectar con el servidor" });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (configToEdit: SQLConfig) => {
    setConfig({
      ...configToEdit,
      password: "" // No mostramos la contraseña por seguridad
    });
  };

  const handleDelete = async (configId: number) => {
    if (!confirm("¿Está seguro de que desea eliminar esta configuración?")) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/api/admin/sql-config/${configId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setMessage({ type: "success", text: "Configuración eliminada exitosamente" });
      await fetchConfigs();
      if (config.id === configId) {
        // Clear form if we just deleted the config being edited
        setConfig({
          username: "",
          password: "",
          server: "",
          database: "",
          driver: "ODBC Driver 17 for SQL Server",
          use_windows_auth: false
        });
      }
    } catch (error) {
      setMessage({ type: "error", text: "Error al conectar con el servidor" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Configuración de SQL Server</h1>

      {/* Lista de configuraciones */}
      {configs.length > 0 && (
        <div className="mb-8 overflow-x-auto">
          <h2 className="text-lg font-semibold mb-4">Configuraciones guardadas</h2>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Servidor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Base de datos</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {configs.map((c) => (
                <tr key={c.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{c.server}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{c.database}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{c.username || 'Windows Auth'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      c.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {c.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(c)}
                      className="mr-2"
                    >
                      <Pencil1Icon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(c.id!)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Formulario de configuración */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">
          {config.id ? 'Editar configuración' : 'Nueva configuración'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Label htmlFor="server">Servidor</Label>
                <Tooltip content={CONNECTION_HELP.server}>
                  <InfoCircledIcon className="h-4 w-4 text-gray-500" />
                </Tooltip>
              </div>
              <Input
                id="server"
                type="text"
                value={config.server}
                onChange={(e) => setConfig({ ...config, server: e.target.value })}
                placeholder="localhost o servidor\instancia"
                required
              />
            </div>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <Label htmlFor="database">Base de datos</Label>
                <Tooltip content={CONNECTION_HELP.database}>
                  <InfoCircledIcon className="h-4 w-4 text-gray-500" />
                </Tooltip>
              </div>
              <Input
                id="database"
                type="text"
                value={config.database}
                onChange={(e) => setConfig({ ...config, database: e.target.value })}
                placeholder="nombre_base_datos"
                required
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="windows-auth"
                checked={config.use_windows_auth}
                onCheckedChange={(checked: boolean) => setConfig({ ...config, use_windows_auth: checked })}
              />
              <div className="flex items-center gap-2">
                <Label htmlFor="windows-auth">Autenticación de Windows</Label>
                <Tooltip content={CONNECTION_HELP.windows_auth}>
                  <InfoCircledIcon className="h-4 w-4 text-gray-500" />
                </Tooltip>
              </div>
            </div>

            {!config.use_windows_auth && (
              <>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Label htmlFor="username">Usuario</Label>
                    <Tooltip content={CONNECTION_HELP.username}>
                      <InfoCircledIcon className="h-4 w-4 text-gray-500" />
                    </Tooltip>
                  </div>
                  <Input
                    id="username"
                    type="text"
                    value={config.username}
                    onChange={(e) => setConfig({ ...config, username: e.target.value })}
                    placeholder="usuario"
                    required={!config.use_windows_auth}
                  />
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Label htmlFor="password">Contraseña</Label>
                    <Tooltip content={CONNECTION_HELP.password}>
                      <InfoCircledIcon className="h-4 w-4 text-gray-500" />
                    </Tooltip>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    value={config.password}
                    onChange={(e) => setConfig({ ...config, password: e.target.value })}
                    placeholder="••••••••"
                    required={!config.use_windows_auth}
                  />
                </div>
              </>
            )}

            <div>
              <div className="flex items-center gap-2 mb-1">
                <Label htmlFor="driver">Driver ODBC</Label>
                <Tooltip content={CONNECTION_HELP.driver}>
                  <InfoCircledIcon className="h-4 w-4 text-gray-500" />
                </Tooltip>
              </div>
              <Select
                value={config.driver}
                onValueChange={(value) => setConfig({ ...config, driver: value })}
              >
                <SelectTrigger id="driver" className="w-full">
                  <SelectValue placeholder="Seleccione un driver" />
                </SelectTrigger>
                <SelectContent>
                  {COMMON_DRIVERS.map((driver) => (
                    <SelectItem key={driver} value={driver}>
                      {driver}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Mensajes y Progreso */}
          {(message.text || progress) && (
            <div className="space-y-4">
              {message.text && (
                <div
                  className={`p-4 rounded-lg border ${
                    message.type === "success"
                      ? "bg-green-50 border-green-200 text-green-700"
                      : message.type === "info"
                      ? "bg-blue-50 border-blue-200 text-blue-700"
                      : "bg-red-50 border-red-200 text-red-700"
                  }`}
                >
                  <pre className="whitespace-pre-wrap font-mono text-sm">
                    {message.text}
                  </pre>
                </div>
              )}
              
              {progress && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Generando embeddings...</span>
                    <span>{progress.processed} / {progress.total} registros</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                      style={{
                        width: `${progress.total > 0 ? (progress.processed / progress.total * 100) : 0}%`
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-4 pt-4">
            <Button
              type="submit"
              className="bg-blue-500 hover:bg-blue-600 text-white"
              disabled={loading}
            >
              {loading ? "Guardando..." : "Guardar configuración"}
            </Button>
            
            <Button
              type="button"
              variant="outline"
              onClick={handleTestConnection}
              disabled={loading}
            >
              {loading ? "Probando..." : "Probar conexión"}
            </Button>

            {config.id && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setConfig({
                    username: "",
                    password: "",
                    server: "",
                    database: "",
                    driver: "ODBC Driver 17 for SQL Server",
                    use_windows_auth: false
                  });
                }}
              >
                Nueva configuración
              </Button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}