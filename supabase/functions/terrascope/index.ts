// index.ts

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, apikey",
};

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  const path = url.pathname;

  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  // Handle GET /data
  if (req.method === "GET" && path.endsWith("/data")) {
    // Replace with your actual data retrieval logic
    const dummyData = [
      { id: 1, name: "Land A", location: "Lagos", size: "500sqm" },
      { id: 2, name: "Land B", location: "Abuja", size: "750sqm" },
    ];
    return new Response(JSON.stringify(dummyData), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
 ...CORS_HEADERS,
      },
    });
  }

  // Handle POST /add
  if (req.method === "POST" && path.endsWith("/add")) {
    const body = await req.json();
    console.log("Received payload:", body);

    // Replace with your actual insert logic
    return new Response(JSON.stringify({ message: "Data added successfully", data: body }), {
      status: 201,
      headers: {
        "Content-Type": "application/json",
        ...CORS_HEADERS,
      },
    });
  }

  // Fallback for unknown routes
  return new Response(JSON.stringify({ error: "Not Found" }), {
    status: 404,
headers: {
      "Content-Type": "application/json",
      ...CORS_HEADERS,
    },
  });
});
