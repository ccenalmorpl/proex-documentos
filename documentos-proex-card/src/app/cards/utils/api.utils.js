import { hubspot } from "@hubspot/ui-extensions";
import { API_CONFIG } from "../config";

export class APIError extends Error {
  constructor(message, statusCode = null) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode;
  }
}

export const fetchFromAPI = async (endpoint, options = {}) => {
  const url = `${API_CONFIG.baseURL}${endpoint}`;

  try {
    const response = await hubspot.fetch(url, {
      method: options.method || "GET",
      timeout: API_CONFIG.timeout,
      body: options.body,
      headers: options.headers,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "");
      throw new APIError(
        `Error ${response.status}: ${response.statusText}${errorText ? ` - ${errorText}` : ""}`,
        response.status
      );
    }

    const data = await response.json();

    if (!data.success) {
      throw new APIError(data.error || "Error en la respuesta de la API");
    }

    return data;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(error.message || "Error de red o parsing", null);
  }
};
