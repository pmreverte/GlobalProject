import { NextRequest, NextResponse } from "next/server";
import { headers } from 'next/headers';
import { SQLServerConfig } from "@/types/sql-config";

export async function GET(request: NextRequest) {
  try {
    const headersList = headers();
    const authHeader = headersList.get('authorization');
    
    if (!authHeader) {
      throw new Error('No authorization token provided');
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/sql-config`, {
      headers: {
        'Authorization': authHeader,
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al obtener la configuración');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error al obtener la configuración SQL:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Error al obtener la configuración" },
      { status: 500 }
    );
  }
}
export async function POST(request: NextRequest) {
  try {
    const rawConfig = await request.json();
    const headersList = headers();
    const authHeader = headersList.get('authorization');
    
    if (!authHeader) {
      throw new Error('No authorization token provided');
    }

    // Validate required fields
    if (!rawConfig.server || typeof rawConfig.server !== 'string') {
      return NextResponse.json({ error: 'El nombre del servidor es requerido' }, { status: 400 });
    }
    if (!rawConfig.database || typeof rawConfig.database !== 'string') {
      return NextResponse.json({ error: 'El nombre de la base de datos es requerido' }, { status: 400 });
    }
    if (typeof rawConfig.use_windows_auth !== 'boolean') {
      return NextResponse.json({ error: 'El tipo de autenticación es requerido' }, { status: 400 });
    }

    // Validate auth credentials if not using Windows auth
    if (!rawConfig.use_windows_auth) {
      if (!rawConfig.username || typeof rawConfig.username !== 'string') {
        return NextResponse.json({ error: 'El nombre de usuario es requerido para autenticación SQL' }, { status: 400 });
      }
      if (!rawConfig.password || typeof rawConfig.password !== 'string') {
        return NextResponse.json({ error: 'La contraseña es requerida para autenticación SQL' }, { status: 400 });
      }
    }

    // Filter and type the configuration
    const config: SQLServerConfig = {
      server: rawConfig.server,
      database: rawConfig.database,
      use_windows_auth: rawConfig.use_windows_auth,
      encrypt: rawConfig.encrypt === true,
      trust_server_certificate: rawConfig.trust_server_certificate === true
    };

    // Add SQL auth credentials only if not using Windows auth
    if (!rawConfig.use_windows_auth) {
      config.username = rawConfig.username;
      config.password = rawConfig.password;
    }
    
    // Save to backend database
    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/sql-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify(config)
    });

    if (!backendResponse.ok) {
      const error = await backendResponse.json();
      throw new Error(error.detail || 'Error al guardar la configuración');
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error al guardar la configuración SQL:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Error al guardar la configuración" },
      { status: 500 }
    );
  }
}