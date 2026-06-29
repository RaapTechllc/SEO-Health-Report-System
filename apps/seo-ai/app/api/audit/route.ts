import { normalizeUrl } from "@/lib/utils";
import { runAudit } from "@/lib/audit/runAudit";
import type { AuditApiError, AuditRequest, AuditResult } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function errorResponse(error: string, status: number): Response {
  const body: AuditApiError = { error };
  return Response.json(body, { status });
}

export async function POST(req: Request): Promise<Response> {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return errorResponse("Request body must be valid JSON.", 400);
  }

  const rawUrl =
    typeof body === "object" && body !== null
      ? (body as Partial<AuditRequest>).url
      : undefined;

  if (typeof rawUrl !== "string") {
    return errorResponse("Missing required field: url.", 400);
  }

  let url: string;
  try {
    url = normalizeUrl(rawUrl);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "That doesn't look like a valid URL.";
    return errorResponse(message, 400);
  }

  try {
    const result: AuditResult = await runAudit(url);
    return Response.json(result);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "An unexpected error occurred.";
    return errorResponse(message, 500);
  }
}
