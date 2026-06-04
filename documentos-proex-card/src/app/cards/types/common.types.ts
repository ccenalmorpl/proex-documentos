export interface SelectOption {
  label: string;
  value: string;
}

export interface PropertyWithOptions {
  value: string | null;
  options?: SelectOption[];
}
