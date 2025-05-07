import { NextRequest, NextResponse } from "next/server";
import { headers } from 'next/headers';
import { SQLServerConfig, ParsedServerInfo } from "@/types/sql-config";

export async function POST(request: NextRequest) {
  let config;
  let parsedServerInfo: ParsedServerInfo | null = null;

  try {
    const headersList = headers();
    const authHeader = headersList.get('authorization');
    
    if (!authHeader) {
      throw new Error('No authorization token provided');
    }

    config = await request.json();
    console.log('Raw SQL config received:', config);

    // Validar y parsear la información del servidor
    if (config?.server) {
      const instanceMatch = config.server.match(/^([^\\]+)\\(.+)$/);
      if (instanceMatch) {
        parsedServerInfo = {
          server: instanceMatch[1],
          instance: instanceMatch[2]
        };
      } else {
        parsedServerInfo = {
          server: config.server
        };
      }
    }
    
    // Validar configuración requerida
    if (!config.server) {
      return NextResponse.json(
        { error: "El nombre del servidor es requerido" },
        { status: 400 }
      );
    }

    if (!config.database) {
      return NextResponse.json(
        { error: "El nombre de la base de datos es requerido" },
        { status: 400 }
      );
    }

    if (!config.use_windows_auth && (!config.username || !config.password)) {
      return NextResponse.json(
        { error: "Usuario y contraseña son requeridos para autenticación SQL" },
        { status: 400 }
      );
    }

    if (!parsedServerInfo) {
      return NextResponse.json(
        { error: "Error al procesar el nombre del servidor" },
        { status: 400 }
      );
    }

    // Validar tipos de datos
    if (typeof config.server !== 'string') {
      return NextResponse.json(
        { error: "El nombre del servidor debe ser texto" },
        { status: 400 }
      );
    }
    if (typeof config.database !== 'string') {
      return NextResponse.json(
        { error: "El nombre de la base de datos debe ser texto" },
        { status: 400 }
      );
    }
    if (typeof config.use_windows_auth !== 'boolean') {
      return NextResponse.json(
        { error: "El tipo de autenticación debe ser booleano" },
        { status: 400 }
      );
    }

    // Preparar la configuración tipada para el backend
    const configToSend: SQLServerConfig = {
      server: parsedServerInfo.server + (parsedServerInfo.instance ? '\\' + parsedServerInfo.instance : ''),
      database: config.database,
      use_windows_auth: config.use_windows_auth,
      encrypt: config.encrypt === true,
      trust_server_certificate: config.trust_server_certificate === true
    };

    // Agregar credenciales SQL solo si no usa autenticación de Windows
    if (!config.use_windows_auth) {
      if (typeof config.username !== 'string') {
        return NextResponse.json(
          { error: "El nombre de usuario debe ser texto" },
          { status: 400 }
        );
      }
      if (typeof config.password !== 'string') {
        return NextResponse.json(
          { error: "La contraseña debe ser texto" },
          { status: 400 }
        );
      }
      configToSend.username = config.username;
      configToSend.password = config.password;
    }

    console.log('Configuración SQL Server:', configToSend);
    
    // Send to backend for testing
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/sql-config/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify(configToSend),
      signal: controller.signal
    }).finally(() => clearTimeout(timeoutId));

    if (!backendResponse.ok) {
      const error = await backendResponse.json();
      throw new Error(error.detail || 'Error al probar la conexión');
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error al probar la conexión SQL:", error);
    
    // Mejorar el mensaje de error para el usuario
    let errorMessage = "Error al conectar con SQL Server: ";
    
    if (error instanceof Error) {
      if (error.message.includes("Failed to connect")) {
        errorMessage += "No se pudo establecer la conexión con el servidor. ";
        
        // Información específica de la instancia
        if (parsedServerInfo) {
          errorMessage += "\nConfiguración detectada:";
          errorMessage += `\n- Servidor: ${parsedServerInfo.server}`;
          if (parsedServerInfo.instance) {
            errorMessage += `\n- Instancia: ${parsedServerInfo.instance}`;
          }
          
          errorMessage += "\n\nVerifique que:";
          errorMessage += "\n1. El servidor SQL Server esté en ejecución";
          errorMessage += "\n2. La instancia SQL Server esté en ejecución";
          errorMessage += "\n3. El driver ODBC esté instalado correctamente";

          const isNamed = Boolean(parsedServerInfo.instance);
          const isLocal = isLocalConnection(parsedServerInfo.server);

          // Información específica del tipo de conexión
          if (isLocal) {
            errorMessage += "\n\nPara conexiones locales, verifique también:";
            errorMessage += "\n- TCP/IP esté habilitado en SQL Server Configuration Manager";
            errorMessage += "\n- SQL Server Configuration Manager > Protocolos > TCP/IP > Direcciones IP tenga la configuración correcta";
            
            if (isNamed) {
              errorMessage += "\n\nPara instancia nombrada local:";
              errorMessage += "\n- El servicio SQL Server Browser esté activo";
            } else {
              errorMessage += "\n\nPara instancia standard local:";
              errorMessage += "\n- La instancia standard esté configurada como la instancia por defecto";
            }
          } else {
            errorMessage += "\n\nPara conexiones remotas, verifique también:";
            errorMessage += "\n- El servidor permita conexiones remotas";
            errorMessage += "\n- El firewall permita conexiones SQL";
            
            if (isNamed) {
              errorMessage += "\n\nPara instancia nombrada remota:";
              errorMessage += "\n- El servicio SQL Server Browser esté activo en el servidor remoto";
            } else {
              errorMessage += "\n\nPara instancia standard remota:";
              errorMessage += "\n- La instancia standard esté configurada como la instancia por defecto";
            }
          }
        }

        // Información de autenticación
        if (config?.use_windows_auth) {
          errorMessage += "\n\nPara autenticación Windows:";
          errorMessage += "\n- La autenticación de Windows esté habilitada en SQL Server";
          errorMessage += "\n- Su usuario de Windows tenga permisos en la base de datos";
          errorMessage += "\n- El servicio SQL Server se ejecute con las credenciales correctas";
        } else {
          errorMessage += "\n\nPara autenticación SQL Server:";
          errorMessage += "\n- Las credenciales proporcionadas sean correctas";
          errorMessage += "\n- El usuario tenga permisos en la base de datos";
        }
      } else if (error.message.includes("Login failed")) {
        errorMessage += "Error de autenticación. Verifique que:";
        if (config.use_windows_auth) {
          errorMessage += "\n1. La autenticación de Windows esté habilitada";
          errorMessage += "\n2. Su usuario de Windows tenga acceso a la base de datos";
        } else {
          errorMessage += "\n1. El nombre de usuario sea correcto";
          errorMessage += "\n2. La contraseña sea correcta";
        }
      } else {
        errorMessage += error.message;
      }
    }

    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}

// Función para detectar si es una conexión local
function isLocalConnection(server: string): boolean {
  const serverLower = server.toLowerCase();
  return serverLower.startsWith('localhost') ||
         serverLower === '127.0.0.1' ||
         serverLower === '(local)' ||
         serverLower.startsWith('.');
}