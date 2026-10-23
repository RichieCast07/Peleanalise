// Cabeceras para llamar al servicio de IA. Si AI_API_KEY está definida, el servicio de IA exige la
// misma clave (X-API-Key), de modo que solo esta aplicación pueda usarlo cuando está en internet.
export function aiHeaders(config: { aiApiKey?: string }): Record<string, string> {
  return config.aiApiKey ? { "X-API-Key": config.aiApiKey } : {};
}
