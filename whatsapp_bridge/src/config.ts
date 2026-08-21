function required(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (value === undefined) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

export const config = {
  internalBaseUrl: required('WHATSAPP_INTERNAL_BASE_URL', 'http://127.0.0.1:8000'),
  internalToken: required('WHATSAPP_INTERNAL_TOKEN'),
  controlToken: required('WHATSAPP_BRIDGE_CONTROL_TOKEN'),
  controlPort: Number(process.env.WHATSAPP_BRIDGE_CONTROL_PORT ?? 8801),
  authDir: required('BAILEYS_AUTH_DIR', 'baileys_auth_info'),
  logLevel: process.env.BAILEYS_LOG_LEVEL ?? 'info',
  logDir: process.env.BAILEYS_LOG_DIR ?? 'logs',
  usePairingCode: (process.env.WHATSAPP_USE_PAIRING_CODE ?? 'true') === 'true',
  phoneNumber: process.env.WHATSAPP_PHONE_NUMBER ?? '',
  pairingCodeFile: process.env.PAIRING_CODE_FILE ?? '.pairing-code.json',
};
