import { NextResponse } from "next/server";
import http from 'http';

export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get("Authorization");
    if (!authHeader) {
      return NextResponse.json(
        { error: "No autorizado" },
        { status: 401 }
      );
    }
    // Extract the token without the "Bearer " prefix
    const token = authHeader.replace("Bearer ", "");

    // Create a promise to handle the HTTP request
    const csvData = await new Promise<string>((resolve, reject) => {
      const apiUrl = new URL(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/reports/export`);
      const options = {
        hostname: apiUrl.hostname,
        port: apiUrl.port || 3000,
        path: apiUrl.pathname,
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/csv'
        }
      };

      const req = http.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          if (res.statusCode !== 200) {
            reject(new Error(`Request failed with status ${res.statusCode}`));
            return;
          }
          resolve(data);
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.end();
    });

    // Return CSV data with appropriate headers
    return new NextResponse(csvData, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename=reports_${new Date().toISOString().split("T")[0]}.csv`,
      },
    });
  } catch (error) {
    console.error("Error exporting reports:", error);
    return NextResponse.json(
      { error: "Error al exportar informes" },
      { status: 500 }
    );
  }
}