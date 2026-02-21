import { hubspot } from "@hubspot/ui-extensions";
import { API_CONFIG } from "../config";

/**
 * Custom error class for API-related errors
 */
export class APIError extends Error {
  constructor(message, statusCode = null) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode;
  }
}

/**
 * Centralized API fetch utility with consistent error handling
 * @param {string} endpoint - API endpoint (will be appended to base URL)
 * @param {Object} options - Fetch options
 * @param {string} options.method - HTTP method (GET, POST, PUT, DELETE)
 * @param {Object} options.body - Request body (will be stringified if needed)
 * @param {Object} options.headers - Additional headers
 * @returns {Promise<Object>} - Parsed JSON response
 * @throws {APIError} - On network or API errors
 */
export const fetchFromAPI = async (endpoint, options = {}) => {
  const url = `${API_CONFIG.baseURL}${endpoint}`;

  try {
    const response = await hubspot.fetch(url, {
      method: options.method || "GET",
      timeout: API_CONFIG.timeout,
      body: options.body
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
    // Network or parsing error
    throw new APIError(error.message || "Error de red o parsing", null);
  }
};
