import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  console.log("GET /api/admin/logs - Request received");
  try {
    const token = request.headers.get("Authorization")?.replace("Bearer ", "");
    if (!token) {
      return NextResponse.json(
        { error: "No token provided" },
        { status: 401 }
      );
    }

    const apiUrl = new URL("/admin/logs", process.env.NEXT_PUBLIC_API_URL);
    const response = await fetch(apiUrl.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("GET /api/admin/logs - Response:", data);
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Error fetching logs:", error);
    return NextResponse.json(
      { error: error.message || "Error al obtener logs" },
      { status: 500 }
    );
  }
}