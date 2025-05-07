import { NextResponse } from "next/server";
import http from 'http';
import https from 'https';

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

    // Get query parameters
    const url = new URL(request.url);
    const startDate = url.searchParams.get("startDate");
    const endDate = url.searchParams.get("endDate");

    // Build the query URL with filters if they exist
    let queryUrl = new URL(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/reports`);
    if (startDate && endDate) {
      queryUrl.searchParams.set("startDate", startDate);
      queryUrl.searchParams.set("endDate", endDate);
    }

    // Create a promise to handle the HTTP request
    const data = await new Promise((resolve, reject) => {
      const options = {
        hostname: '127.0.0.1',
        port: '8000',
        path: `${queryUrl.pathname}${queryUrl.search}`,
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
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
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error('Failed to parse response as JSON'));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.end();
    });

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching reports:", error);
    return NextResponse.json(
      { error: "Error al obtener informes" },
      { status: 500 }
    );
  }
}