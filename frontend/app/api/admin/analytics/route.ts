import { NextResponse } from "next/server";

export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get("Authorization");
    if (!authHeader) {
      return NextResponse.json(
        { error: "No autorizado" },
        { status: 401 }
      );
    }

    // Get time range from query params
    const url = new URL(request.url);
    const range = url.searchParams.get("range") || "week";

    // Use environment variable for API URL - FastAPI already has /api prefix
    const apiUrl = new URL(`${process.env.NEXT_PUBLIC_API_URL}/admin/analytics`);
    apiUrl.searchParams.append("range", range);

    // Forward the token to the backend
    console.log("Making request to:", apiUrl.toString());
    console.log("With headers:", { Authorization: authHeader });

    const response = await fetch(apiUrl.toString(), {
      method: 'GET',
      headers: {
        "Authorization": authHeader,
        "Accept": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response:", errorText);
      throw new Error(`Error: ${response.status} - ${errorText}`);
    }

    try {
      const data = await response.json();
      console.log("Analytics response:", data);
      return NextResponse.json(data);
    } catch (error) {
      console.error("Error parsing response:", error);
      return NextResponse.json(
        { error: "Error al procesar la respuesta" },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error("Error fetching analytics:", error);
    return NextResponse.json(
      { error: "Error al obtener analíticas" },
      { status: 500 }
    );
  }
}