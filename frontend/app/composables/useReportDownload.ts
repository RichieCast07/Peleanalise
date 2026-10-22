import { useApiFetch } from "~/composables/useApiFetch";
import { useNotification } from "~/composables/useNotification";

// Un <a href="/api/reports/..."> no envía el token Authorization y la API responde 401,
// así que el PDF se pide con useApiFetch (que añade el token) y se descarga desde un Blob.
export function useReportDownload() {
  const notif       = useNotification();
  const downloading = ref<string | null>(null);

  async function errorMessage(err: unknown): Promise<string> {
    const e = err as { data?: unknown; message?: string };
    try {
      if (e?.data instanceof Blob) {
        const parsed = JSON.parse(await e.data.text());
        if (parsed?.message) return String(parsed.message);
      } else if ((e?.data as { message?: string })?.message) {
        return String((e.data as { message?: string }).message);
      }
    } catch { /* se usa el mensaje genérico */ }
    return "No se pudo generar el reporte";
  }

  async function download(studyId: string) {
    if (downloading.value) return;
    downloading.value = studyId;
    try {
      const blob = await useApiFetch<Blob>(`/api/reports/${studyId}`, { responseType: "blob" } as never);

      const url = URL.createObjectURL(blob);
      const a   = document.createElement("a");
      a.href     = url;
      a.download = `reporte-${studyId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10_000);

      notif.success("Reporte descargado");
    } catch (err) {
      notif.error("No se pudo descargar el PDF", await errorMessage(err));
    } finally {
      downloading.value = null;
    }
  }

  return { download, downloading };
}
