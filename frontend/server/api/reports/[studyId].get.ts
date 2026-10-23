import { prisma } from "../../utils/prisma";
import { getAuthUser } from "../../utils/rbac";
import { auditLog } from "../../utils/audit";
import { absoluteImageUrl } from "../../utils/storage";
import { aiHeaders } from "../../utils/ai";

export default defineEventHandler(async (event) => {
  const auth    = getAuthUser(event);
  const studyId = getRouterParam(event, "studyId")!;
  const config  = useRuntimeConfig();

  const study = await prisma.study.findFirst({
    where: { id: studyId, deletedAt: null },
    include: {
      patient:    true,
      capturedBy: { select: { firstName: true, lastName: true, role: true } },
      images:     true,
      analysis: {
        include: { abcde: true, prediction: true },
      },
    },
  });

  if (!study)          throw createError({ statusCode: 404, message: "Estudio no encontrado" });
  if (!study.analysis) throw createError({ statusCode: 400, message: "El estudio aún no ha sido analizado" });

  // Construir URLs absolutas para que Python las descargue
  const host = getRequestHeader(event, "host") ?? "localhost:3000";
  const imageUrls: Record<string, string> = {};
  for (const img of study.images) {
    imageUrls[img.type] = absoluteImageUrl(img.storagePath, host);
  }

  let pdfResponse: { pdf_base64: string };
  try {
    pdfResponse = await $fetch<{ pdf_base64: string }>(
      `${config.pythonAiUrl}/report/generate`,
      {
        method:  "POST",
        body:    { study, image_urls: imageUrls },
        headers: aiHeaders(config),
        timeout: 60_000,
      }
    );
  } catch (err) {
    console.error("[Report]", err);
    const e = err as { statusCode?: number; status?: number; data?: { detail?: unknown } };
    if ((e.statusCode ?? e.status) && e.data?.detail) {
      throw createError({ statusCode: 502, message: `Servicio de IA: ${String(e.data.detail)}` });
    }
    throw createError({
      statusCode: 503,
      message: `No se pudo conectar con el servicio de IA (${config.pythonAiUrl}) para generar el PDF. Verifica que esté iniciado.`,
    });
  }

  await auditLog(event, "EXPORT", "studies", studyId, auth.userId);

  setResponseHeader(event, "Content-Type", "application/pdf");
  setResponseHeader(event, "Content-Disposition", `attachment; filename="reporte-${studyId.slice(0, 8)}.pdf"`);
  return Buffer.from(pdfResponse.pdf_base64, "base64");
});
