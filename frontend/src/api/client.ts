const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token } = options;
  const isFormData = body instanceof FormData;

  const headers: Record<string, string> = {};
  if (!isFormData) {
    // For FormData, the browser sets Content-Type itself (including the
    // multipart boundary) — setting it manually here would break the upload.
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    // HTTPException(detail="...") -> {"detail": "some string"}
    if (typeof data.detail === "string") {
      return data.detail;
    }
    // FastAPI's automatic 422 request validation -> {"detail": [{"msg": "...", ...}, ...]}
    if (Array.isArray(data.detail)) {
      return data.detail.map((e: { msg: string }) => e.msg).join(", ");
    }
    return "Something went wrong.";
  } catch {
    return "Something went wrong.";
  }
}
