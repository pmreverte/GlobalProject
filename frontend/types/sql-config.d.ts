export interface SQLServerConfig {
  server: string;
  database: string;
  use_windows_auth: boolean;
  username?: string;
  password?: string;
  encrypt?: boolean;
  trust_server_certificate?: boolean;
}

export interface ParsedServerInfo {
  server: string;
  instance?: string;
}