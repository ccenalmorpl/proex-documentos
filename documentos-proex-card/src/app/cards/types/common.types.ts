/**
 * Common TypeScript interfaces and types for the Documentos PROEX application
 */

// ============================================================================
// SELECT OPTIONS
// ============================================================================

export interface SelectOption {
  label: string;
  value: string;
}

export interface PropertyWithOptions {
  value: string | null;
  options?: SelectOption[];
}
