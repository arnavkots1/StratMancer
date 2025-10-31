export const runtime = 'node'; // ensure Node runtime

// Exclude from middleware/rewrites - this route must be accessible directly

export async function GET() {
  const body = 'c0610647-bb2e-46d6-b455-492ada6c1006'; // Current verification code
  return new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store, no-cache, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  });
}

// Handle HEAD requests - some verifiers probe with HEAD
export async function HEAD() {
  const body = 'c0610647-bb2e-46d6-b455-492ada6c1006';
  return new Response(null, {
    status: 200,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store, no-cache, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Length': String(body.length),
    },
  });
}

